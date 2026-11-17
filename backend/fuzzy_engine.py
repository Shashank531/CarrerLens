"""
CareerLens — Phase 5: Fuzzy Inference Engine (Precision Upgraded)
==================================================================
Takes a user's skill profile (0-10 per skill, from Phase 4) and scores
every career in careers.csv using Mamdani fuzzy inference with
centroid defuzzification, driven by rules.csv and career_skill_matrix.csv.

Each skill input (0-10) is fuzzified into 5 linguistic levels:
    Very Low | Low | Medium | High | Very High
Each career's compatibility output (0-100) is fuzzified into 4 levels:
    Low | Medium | High | Excellent
rules.csv supplies up to 4 antecedents (skill+level) -> one consequent
(career compatibility level) per rule.

The inference is evaluated directly with numpy (min implication, max
aggregation, trapezoidal centroid) instead of building one
scikit-fuzzy ControlSystemSimulation per career. Scores are identical to the
previous implementation — backend/test_fuzzy_numerics.py compares both — but
scoring holds no per-request state, so one engine can serve concurrent
requests and a career's score can no longer depend on which profiles were
scored before it. All 105 careers are scored in ~2ms instead of ~9ms.

Usage:
    from fuzzy_engine import FuzzyEngine

    engine = FuzzyEngine(data_dir="../data/csv")
    ranked = engine.score_all(skill_profile)   # skill_profile from Phase 4
    top5 = ranked[:5]
"""

import csv
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


LEVELS_IN = ["Very Low", "Low", "Medium", "High", "Very High"]
LEVELS_OUT = ["Low", "Medium", "High", "Excellent"]

# ── Tunable Precision & Scaling Constants ─────────────────────────────
MISSING_SKILL_DEFAULT = 0.0       # Unanswered skills treated as gaps across all sub-scores
CONTRAST = 1.5                   # 1.0 = linear fit-preserving, >1.0 sharpens distinction at the top
FUZZY_WEIGHT = 0.45              # Mamdani inference contribution
MATRIX_WEIGHT = 0.55             # Skill matrix multi-factor contribution
NO_FUZZY_MATRIX_WEIGHT = 0.80    # Fallback matrix weight if fuzzy rules produce 0 output
MIN_COMPATIBILITY = 12.0         # Lower bound for compatibility scale
MAX_COMPATIBILITY = 96.0         # Upper bound for compatibility scale


# ── Universe of discourse & membership functions ──────────────────────
SKILL_UNIVERSE = np.arange(0.0, 10.01, 0.1)
COMPAT_UNIVERSE = np.arange(0.0, 100.01, 1.0)


def _trimf(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """Triangular membership function, matching skfuzzy.fuzz.trimf exactly."""
    y = np.zeros_like(x, dtype=float)
    if a != b:
        idx = (a < x) & (x < b)
        y[idx] = (x[idx] - a) / (b - a)
    if b != c:
        idx = (b < x) & (x < c)
        y[idx] = (c - x[idx]) / (c - b)
    y[x == b] = 1.0
    return y


# Row order matches LEVELS_IN / LEVELS_OUT.
_SKILL_MF = np.vstack([
    _trimf(SKILL_UNIVERSE, 0, 0, 2.5),      # Very Low
    _trimf(SKILL_UNIVERSE, 0, 2.5, 5),      # Low
    _trimf(SKILL_UNIVERSE, 2.5, 5, 7.5),    # Medium
    _trimf(SKILL_UNIVERSE, 5, 7.5, 10),     # High
    _trimf(SKILL_UNIVERSE, 7.5, 10, 10),    # Very High
])
# Tiered triangles per output level, row order matches LEVELS_OUT.
_COMPAT_TRIANGLES = [
    (0.0, 0.0, 35.0),     # Low
    (20.0, 45.0, 68.0),   # Medium
    (55.0, 74.0, 90.0),   # High
    (78.0, 100.0, 100.0),  # Excellent
]
_COMPAT_MF = np.vstack([_trimf(COMPAT_UNIVERSE, a, b, c) for a, b, c in _COMPAT_TRIANGLES])

_IN_INDEX = {name: i for i, name in enumerate(LEVELS_IN)}
_OUT_INDEX = {name: i for i, name in enumerate(LEVELS_OUT)}


def _centroid(universe: np.ndarray, aggregated: np.ndarray) -> float:
    """
    Centroid of a piecewise-linear membership function, integrated with the
    trapezoid rule (the same defuzzification scikit-fuzzy performs).
    """
    y1, y2 = aggregated[:-1], aggregated[1:]
    x1, x2 = universe[:-1], universe[1:]

    area = 0.5 * (x2 - x1) * (y1 + y2)
    heights = y1 + y2
    nonzero = heights > 0
    if not nonzero.any():
        return 0.0

    area_nz = area[nonzero]
    moment = area_nz * (
        x1[nonzero] * (2 * y1[nonzero] + y2[nonzero])
        + x2[nonzero] * (y1[nonzero] + 2 * y2[nonzero])
    ) / (3 * heights[nonzero])

    total_area = area_nz.sum()
    if total_area == 0:
        return 0.0
    return float(moment.sum() / total_area)


class FuzzyEngine:
    def __init__(self, data_dir: str):
        data_dir = Path(data_dir)
        self._data_dir = data_dir
        self.rules_by_career = self._load_rules(data_dir / "rules.csv")
        self.careers = self._load_careers(data_dir / "careers.csv")

        matrix_path = data_dir / "career_skill_matrix.csv"
        if matrix_path.exists():
            self.load_skill_matrix(str(matrix_path))

        # Every skill referenced by any rule becomes one row of the membership
        # matrix that each profile is fuzzified into.
        self.skills = sorted({s for rules in self.rules_by_career.values()
                              for r in rules for s, _ in r["antecedents"]})
        self._skill_row = {s: i for i, s in enumerate(self.skills)}
        self._compiled = self._compile_rules()

    # ---------- Loading ----------

    def _load_rules(self, path: Path) -> Dict[str, List[dict]]:
        rules_by_career: Dict[str, List[dict]] = {}
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                career = row["THEN_Career"]
                antecedents = []
                for i in range(1, 5):
                    skill = row.get(f"IF{i}_Skill", "").strip()
                    level = row.get(f"IF{i}_Level", "").strip()
                    if skill and level:
                        antecedents.append((skill, level))
                rules_by_career.setdefault(career, []).append({
                    "antecedents": antecedents,
                    "consequent": row["THEN_Level"].strip(),
                })
        return rules_by_career

    def _load_careers(self, path: Path) -> List[str]:
        with open(path, newline="", encoding="utf-8") as f:
            return [row["Career Name"] for row in csv.DictReader(f)]

    def _compile_rules(self) -> Dict[str, List[Tuple[np.ndarray, np.ndarray, int]]]:
        """
        Flatten each career's rules into index arrays so scoring is pure numpy:
        (skill rows, level columns, consequent level index) per rule.
        """
        compiled: Dict[str, List[Tuple[np.ndarray, np.ndarray, int]]] = {}
        for career, rules in self.rules_by_career.items():
            career_rules = []
            for r in rules:
                if not r["antecedents"]:
                    continue
                rows = np.array([self._skill_row[s] for s, _ in r["antecedents"]], dtype=np.intp)
                cols = np.array([_IN_INDEX[lvl] for _, lvl in r["antecedents"]], dtype=np.intp)
                career_rules.append((rows, cols, _OUT_INDEX[r["consequent"]]))
            if career_rules:
                compiled[career] = career_rules
        return compiled

    # ---------- Fuzzy machinery ----------

    def _fuzzify(self, skill_profile: Dict[str, float]) -> np.ndarray:
        """Membership of every known skill in each of the 5 input levels."""
        values = np.array([skill_profile.get(s, MISSING_SKILL_DEFAULT) for s in self.skills],
                          dtype=float)
        membership = np.empty((len(self.skills), len(LEVELS_IN)))
        for j in range(len(LEVELS_IN)):
            membership[:, j] = np.interp(values, SKILL_UNIVERSE, _SKILL_MF[j])
        return membership

    def _score_with_membership(self, career: str, membership: np.ndarray) -> float:
        """
        Mamdani inference for one career: min implication per rule, max
        aggregation of the clipped consequent curves, centroid defuzzification.
        """
        rules = self._compiled.get(career)
        if not rules:
            return 0.0

        fired = []
        for rows, cols, level in rules:
            strength = float(membership[rows, cols].min())
            if strength > 0.0:
                fired.append((strength, level))

        if not fired:
            # No rule fired at all (all memberships ~0)
            return 0.0

        # Clipping a consequent triangle at its activation level introduces two
        # x-values where the curve leaves the flat top. Adding those to the
        # universe keeps the aggregated curve piecewise-linear in every
        # interval, so the trapezoid centroid is exact (this is what
        # scikit-fuzzy's upsampling does).
        extra = []
        for strength, level in fired:
            a, b, c = _COMPAT_TRIANGLES[level]
            if a < b:
                extra.append(a + strength * (b - a))
            if b < c:
                extra.append(c - strength * (c - b))
        universe = np.union1d(COMPAT_UNIVERSE, extra) if extra else COMPAT_UNIVERSE

        aggregated = np.zeros_like(universe)
        for strength, level in fired:
            curve = np.interp(universe, COMPAT_UNIVERSE, _COMPAT_MF[level])
            np.fmax(aggregated, np.minimum(strength, curve), out=aggregated)

        return round(_centroid(universe, aggregated), 1)

    # ---------- Public API ----------

    def score_career(self, career: str, skill_profile: Dict[str, float]) -> float:
        """
        Run Mamdani inference + centroid defuzzification for one career.
        Returns a compatibility percentage 0-100.
        Missing skills in the user's profile default to MISSING_SKILL_DEFAULT (0.0).
        """
        return self._score_with_membership(career, self._fuzzify(skill_profile))

    def _skill_matrix_score(
        self,
        career: str,
        skill_profile: Dict[str, float],
        confidence: Optional[Dict[str, int]] = None
    ) -> float:
        """
        Compute an advanced multi-factor 0-100 fit score based on:
        1. Profile Shape Correlation (Pearson alignment of signature strengths)
        2. Strict Weighted Requirement Satisfaction (heavy penalty for missing core skills)
        3. Signature Skill Dominance (fit on the career's highest demanding skills)
        """
        if not hasattr(self, "_skill_matrix"):
            return 50.0

        reqs = self._skill_matrix.get(career, {})
        if not reqs:
            return 50.0

        # 1. Profile Shape Correlation (relative strengths vs career demand)
        u_vals = [skill_profile.get(s, MISSING_SKILL_DEFAULT) for s in reqs]
        r_vals = [reqs[s] for s in reqs]
        u_mean = sum(u_vals) / len(u_vals)
        r_mean = sum(r_vals) / len(r_vals)

        u_diff = [u - u_mean for u in u_vals]
        r_diff = [r - r_mean for r in r_vals]

        dot = sum(ud * rd for ud, rd in zip(u_diff, r_diff))
        norm_u = math.sqrt(sum(ud**2 for ud in u_diff))
        norm_r = math.sqrt(sum(rd**2 for rd in r_diff))
        corr = dot / (norm_u * norm_r) if (norm_u > 0 and norm_r > 0) else 0.0
        shape_score = 50.0 + corr * 50.0

        # 2. Weighted Requirement Satisfaction with strict deficit penalties and optional confidence
        satisfaction = 0.0
        total_w = 0.0
        for s, r in reqs.items():
            u = skill_profile.get(s, MISSING_SKILL_DEFAULT)
            
            # Confidence weighting factor (floor at 0.4 so 1-question skills still contribute)
            if confidence:
                conf = confidence.get(s, 1)
                conf_factor = max(0.4, min(1.0, conf / 3.0))
            else:
                conf_factor = 1.0

            w = ((r / 10.0) ** 2.5) * conf_factor
            if u >= r:
                fit = 100.0 - (u - r) * 2.0
            else:
                gap = r - u
                fit = max(0.0, 100.0 - (gap / 10.0) * 160.0)
            satisfaction += fit * w
            total_w += w
        sat_score = satisfaction / total_w if total_w > 0 else 50.0

        # 3. Top Signature Skills Fit
        top_reqs = sorted(reqs.items(), key=lambda x: -x[1])[:3]
        top_sat = sum(min(10.0, skill_profile.get(s, MISSING_SKILL_DEFAULT)) / r for s, r in top_reqs) / len(top_reqs) * 100.0

        return 0.35 * sat_score + 0.45 * shape_score + 0.20 * min(100.0, top_sat)

    def load_skill_matrix(self, csv_path: str):
        """Load career_skill_matrix.csv so score_all can use it."""
        self._skill_matrix: Dict[str, Dict[str, float]] = {}
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            skill_cols = [c for c in reader.fieldnames if c != "Career"]
            for row in reader:
                self._skill_matrix[row["Career"]] = {
                    s: float(row[s]) for s in skill_cols
                }

    def score_all(
        self,
        skill_profile: Dict[str, float],
        confidence: Optional[Dict[str, int]] = None
    ) -> List[dict]:
        """
        Score every career with real fit-preserving discrimination.
        Returns a descending list of {"career": str, "compatibility": float, "raw_score": float}.
        """
        membership = self._fuzzify(skill_profile)

        raw_list = []
        for career in self.careers:
            fuzzy_score = self._score_with_membership(career, membership)
            matrix_score = self._skill_matrix_score(career, skill_profile, confidence=confidence)
            if fuzzy_score > 0:
                combined = FUZZY_WEIGHT * fuzzy_score + MATRIX_WEIGHT * matrix_score
            else:
                combined = NO_FUZZY_MATRIX_WEIGHT * matrix_score
            raw_list.append({"career": career, "raw_score": combined})

        raw_list.sort(key=lambda r: -r["raw_score"])

        scores = [item["raw_score"] for item in raw_list]
        hi, lo = max(scores), min(scores)
        spread = hi - lo if hi != lo else 1.0

        for item in raw_list:
            # Monotonic, gap-preserving transform driven strictly by real fit distance
            norm_s = (item["raw_score"] - lo) / spread
            t = norm_s ** CONTRAST
            final_pct = MIN_COMPATIBILITY + t * (MAX_COMPATIBILITY - MIN_COMPATIBILITY)
            item["compatibility"] = round(final_pct, 1)

        return raw_list


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from feature_extraction import load_questions, extract_features
    import random

    here = Path(__file__).parent
    data_dir = here.parent / "data" / "csv"

    questions = load_questions(str(data_dir / "questions.csv"))
    random.seed(7)
    demo_answers = {}
    for q in questions:
        if q["skill"] in ("Programming", "Logical Thinking", "Math", "Problem Solving", "Learning Ability"):
            demo_answers[q["id"]] = random.choice([4, 5, 5])
        else:
            demo_answers[q["id"]] = random.choice([2, 3, 3, 4])

    skill_profile = extract_features(demo_answers, questions)

    print("Building fuzzy engine (this scans all 420 rules across 105 careers)...")
    engine = FuzzyEngine(data_dir=str(data_dir))

    print("\nScoring all careers...\n")
    ranked = engine.score_all(skill_profile)

    print(f"{'Rank':<6}{'Career':<28}{'Compatibility'}")
    print("-" * 50)
    for i, r in enumerate(ranked[:10], 1):
        print(f"{i:<6}{r['career']:<28}{r['compatibility']}%")
