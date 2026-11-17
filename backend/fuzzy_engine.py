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

Usage:
    from fuzzy_engine import FuzzyEngine

    engine = FuzzyEngine(data_dir="../data/csv")
    ranked = engine.score_all(skill_profile)   # skill_profile from Phase 4
    top5 = ranked[:5]
"""

import csv
import math
import threading
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


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


class FuzzyEngine:
    def __init__(self, data_dir: str):
        data_dir = Path(data_dir)
        self._data_dir = data_dir
        self.rules_by_career = self._load_rules(data_dir / "rules.csv")
        self.careers = self._load_careers(data_dir / "careers.csv")
        
        matrix_path = data_dir / "career_skill_matrix.csv"
        if matrix_path.exists():
            self.load_skill_matrix(str(matrix_path))
            
        # ControlSystemSimulation mutates its own state on every compute(), so a
        # simulation object must never be shared between threads. The cache is
        # therefore per-thread rather than per-instance.
        self._local = threading.local()

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

    # ---------- Fuzzy machinery ----------

    def _make_skill_antecedent(self, name: str) -> ctrl.Antecedent:
        """0-10 skill input with 5 overlapping triangular membership functions."""
        universe = np.arange(0, 10.01, 0.1)
        var = ctrl.Antecedent(universe, name)
        var["Very Low"] = fuzz.trimf(universe, [0, 0, 2.5])
        var["Low"] = fuzz.trimf(universe, [0, 2.5, 5])
        var["Medium"] = fuzz.trimf(universe, [2.5, 5, 7.5])
        var["High"] = fuzz.trimf(universe, [5, 7.5, 10])
        var["Very High"] = fuzz.trimf(universe, [7.5, 10, 10])
        return var

    def _make_compatibility_consequent(self) -> ctrl.Consequent:
        """0-100 compatibility output with 4 overlapping triangular membership functions."""
        universe = np.arange(0, 100.01, 1)
        var = ctrl.Consequent(universe, "compatibility")
        var["Low"] = fuzz.trimf(universe, [0, 0, 35])
        var["Medium"] = fuzz.trimf(universe, [20, 45, 68])
        var["High"] = fuzz.trimf(universe, [55, 74, 90])
        var["Excellent"] = fuzz.trimf(universe, [78, 100, 100])
        return var

    def _build_system(self, career: str) -> ctrl.ControlSystemSimulation:
        career_rules = self.rules_by_career.get(career, [])
        skills_used = sorted({skill for r in career_rules for skill, _ in r["antecedents"]})

        antecedents = {s: self._make_skill_antecedent(s) for s in skills_used}
        compatibility = self._make_compatibility_consequent()

        fuzzy_rules = []
        for r in career_rules:
            if not r["antecedents"]:
                continue
            term = None
            for skill, level in r["antecedents"]:
                clause = antecedents[skill][level]
                term = clause if term is None else (term & clause)
            fuzzy_rules.append(ctrl.Rule(term, compatibility[r["consequent"]]))

        system = ctrl.ControlSystem(fuzzy_rules)
        return ctrl.ControlSystemSimulation(system)

    def _get_system(self, career: str) -> ctrl.ControlSystemSimulation:
        cache = getattr(self._local, "systems", None)
        if cache is None:
            cache = self._local.systems = {}
        if career not in cache:
            cache[career] = self._build_system(career)
        return cache[career]

    # ---------- Public API ----------

    def score_career(self, career: str, skill_profile: Dict[str, float]) -> float:
        """
        Run Mamdani inference + centroid defuzzification for one career.
        Returns a compatibility percentage 0-100.
        Missing skills in the user's profile default to MISSING_SKILL_DEFAULT (0.0).
        """
        career_rules = self.rules_by_career.get(career, [])
        skills_used = sorted({skill for r in career_rules for skill, _ in r["antecedents"]})
        if not skills_used:
            return 0.0

        sim = self._get_system(career)
        for skill in skills_used:
            sim.input[skill] = skill_profile.get(skill, MISSING_SKILL_DEFAULT)

        try:
            sim.compute()
            return round(float(sim.output["compatibility"]), 1)
        except Exception:
            # No rule fired strongly enough to produce output (all memberships ~0)
            return 0.0

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
        raw_list = []
        for career in self.careers:
            fuzzy_score = self.score_career(career, skill_profile)
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