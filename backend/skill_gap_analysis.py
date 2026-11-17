"""
CareerLens — Phase 7: Skill-Gap Analysis
===========================================
For each recommended career, compares the user's skill profile against
that career's required skill levels (career_skill_matrix.csv) and
returns a sorted gap table — largest gap first, so the user knows what
to work on before what's already close.

    Skill Gap = Required career level - User's current level

Skills where the user already meets or exceeds the requirement are
still included (gap <= 0) but sink to the bottom, since a mini
project audience benefits from seeing the full picture, not just the
weak points.

Usage:
    from skill_gap_analysis import SkillGapAnalyzer

    analyzer = SkillGapAnalyzer(data_dir="../data/csv")
    gaps = analyzer.analyze("AI/ML Engineer", skill_profile)
    for row in analyzer.analyze_for_recommendations(skill_profile, top5):
        ...
"""

import csv
from pathlib import Path
from typing import Dict, List


class SkillGapAnalyzer:
    def __init__(self, data_dir: str):
        data_dir = Path(data_dir)
        self.skill_matrix = self._load_skill_matrix(data_dir / "career_skill_matrix.csv")

    def _load_skill_matrix(self, path: Path) -> Dict[str, Dict[str, float]]:
        matrix = {}
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            skill_cols = [c for c in reader.fieldnames if c != "Career"]
            for row in reader:
                matrix[row["Career"]] = {s: float(row[s]) for s in skill_cols}
        return matrix

    def analyze(self, career: str, skill_profile: Dict[str, float], top_n: int = None) -> List[dict]:
        """
        Returns a list of {skill, user_score, required_score, gap},
        sorted by gap descending (biggest weakness first). Skills the
        user hasn't answered default to 0 so gaps aren't hidden by
        missing data.
        """
        requirements = self.skill_matrix.get(career, {})
        rows = []
        for skill, required in requirements.items():
            user_score = skill_profile.get(skill, 0.0)
            gap = round(required - user_score, 2)
            rows.append({
                "skill": skill,
                "user_score": round(user_score, 2),
                "required_score": required,
                "gap": gap,
            })
        rows.sort(key=lambda r: -r["gap"])
        return rows[:top_n] if top_n else rows

    def analyze_for_recommendations(
        self, skill_profile: Dict[str, float], recommendations: List[dict], top_n_skills: int = 6
    ) -> List[dict]:
        """
        Takes the output of RecommendationEngine.recommend() (Phase 6)
        and attaches a skill-gap table to each recommended career.
        Only the top_n_skills biggest gaps are kept per career, to
        keep the eventual UI table focused rather than showing all 20.
        """
        enriched = []
        for rec in recommendations:
            gap_table = self.analyze(rec["career"], skill_profile, top_n=top_n_skills)
            enriched.append({**rec, "skill_gaps": gap_table})
        return enriched


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from feature_extraction import load_questions, extract_features
    from fuzzy_engine import FuzzyEngine
    from recommendation_engine import RecommendationEngine
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

    gap_analyzer = SkillGapAnalyzer(data_dir=str(data_dir))
    enriched = gap_analyzer.analyze_for_recommendations(skill_profile, top5)

    for r in enriched:
        print(f"\n{r['career']} — {r['compatibility']}% match")
        print(f"{'Skill':<22}{'Yours':<10}{'Required':<10}{'Gap'}")
        print("-" * 50)
        for row in r["skill_gaps"]:
            print(f"{row['skill']:<22}{row['user_score']:<10}{row['required_score']:<10}{row['gap']}")
