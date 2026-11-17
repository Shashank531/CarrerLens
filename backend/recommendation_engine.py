"""
CareerLens — Phase 6: Recommendation Engine
==============================================
Takes the ranked output of the fuzzy engine (Phase 5) and produces the
top 5 careers with a plain-language explanation for each, based on
which of the user's traits most strongly support that specific match.

An explanation names a trait if two things are both true:
  1. The user scored it Medium-High or above (score >= 6.5 / 10)
  2. The career's skill matrix also values it highly (requirement >= 6 / 10)
A trait that's high for the user but irrelevant to the career (or vice
versa) is not cited — the explanation should reflect real overlap,
not just the user's best stats in isolation.

Usage:
    from recommendation_engine import RecommendationEngine

    engine = RecommendationEngine(data_dir="../data/csv")
    top5 = engine.recommend(skill_profile, ranked_careers, top_n=5)
"""

import csv
from pathlib import Path
from typing import Dict, List


class RecommendationEngine:
    def __init__(self, data_dir: str):
        data_dir = Path(data_dir)
        self.skill_matrix = self._load_skill_matrix(data_dir / "career_skill_matrix.csv")
        self.career_meta = self._load_career_meta(data_dir / "careers.csv")

    def _load_skill_matrix(self, path: Path) -> Dict[str, Dict[str, float]]:
        matrix = {}
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            skill_cols = [c for c in reader.fieldnames if c != "Career"]
            for row in reader:
                matrix[row["Career"]] = {s: float(row[s]) for s in skill_cols}
        return matrix

    def _load_career_meta(self, path: Path) -> Dict[str, dict]:
        meta = {}
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                meta[row["Career Name"]] = {
                    "category": row.get("Category", ""),
                    "description": row.get("Description", ""),
                    "salary": row.get("Avg Salary (LPA)", ""),
                    "demand": row.get("Future Demand", ""),
                    "education": row.get("Required Education", ""),
                }
        return meta

    def _explain(self, career: str, skill_profile: Dict[str, float], max_reasons: int = 4) -> str:
        """
        Find skills where the user is strong (>=6.5) AND the career
        requires it (>=6), ranked by how much the user exceeds a
        baseline mid-point (5) weighted by the career's requirement —
        so the reasons cited are the ones actually driving the match,
        not just the user's highest scores overall.
        """
        requirements = self.skill_matrix.get(career, {})
        overlaps = []
        for skill, required in requirements.items():
            user_score = skill_profile.get(skill, 0.0)
            if user_score >= 6.5 and required >= 6.0:
                relevance = user_score * (required / 10)
                overlaps.append((skill, user_score, relevance))

        overlaps.sort(key=lambda x: -x[2])
        top_reasons = [skill for skill, _, _ in overlaps[:max_reasons]]

        if not top_reasons:
            return "This match is driven by a broad, balanced profile rather than one standout trait."

        if len(top_reasons) == 1:
            reason_text = top_reasons[0]
        else:
            reason_text = ", ".join(top_reasons[:-1]) + f", and {top_reasons[-1]}"

        return f"Recommended because: {reason_text}."

    def recommend(self, skill_profile: Dict[str, float], ranked_careers: List[dict], top_n: int = 5) -> List[dict]:
        """
        ranked_careers is the output of FuzzyEngine.score_all() —
        a list of {"career": ..., "compatibility": ...} sorted descending.
        Returns the top_n with explanation + supporting metadata attached.
        """
        top = ranked_careers[:top_n]
        results = []
        for entry in top:
            career = entry["career"]
            meta = self.career_meta.get(career, {})
            results.append({
                "career": career,
                "compatibility": entry["compatibility"],
                "explanation": self._explain(career, skill_profile),
                "category": meta.get("category", ""),
                "description": meta.get("description", ""),
                "avg_salary_lpa": meta.get("salary", ""),
                "future_demand": meta.get("demand", ""),
                "required_education": meta.get("education", ""),
            })
        return results


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from feature_extraction import load_questions, extract_features
    from fuzzy_engine import FuzzyEngine
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

    fuzzy = FuzzyEngine(data_dir=str(data_dir))
    ranked = fuzzy.score_all(skill_profile)

    rec_engine = RecommendationEngine(data_dir=str(data_dir))
    top5 = rec_engine.recommend(skill_profile, ranked, top_n=5)

    print("Top 5 Career Recommendations\n" + "=" * 60)
    for i, r in enumerate(top5, 1):
        print(f"\n{i}. {r['career']} — {r['compatibility']}% match")
        print(f"   {r['category']} · {r['avg_salary_lpa']} LPA avg · {r['future_demand']} demand")
        print(f"   {r['explanation']}")
