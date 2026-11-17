"""
CareerLens — Phase 8: Learning Roadmap
=========================================
Reads a career's ordered learning steps from roadmaps.csv and returns
them as a practical sequence, with steps that target the user's
biggest skill gaps flagged as priority.

Note: roadmap steps are kept in their original Step Order rather than
being resorted by gap size. The CSV's ordering encodes prerequisites
("foundations before ML models"), so re-sorting purely by gap size
would produce a sequence that ignores dependencies. Instead, each step
is annotated with is_priority (True if it targets one of the user's
top skill gaps) so the UI can visually highlight it without breaking
the logical order.

Usage:
    from roadmap_builder import RoadmapBuilder

    builder = RoadmapBuilder(data_dir="../data/csv")
    roadmap = builder.build("AI/ML Engineer", skill_gaps)
"""

import csv
from pathlib import Path
from typing import Dict, List


class RoadmapBuilder:
    def __init__(self, data_dir: str):
        data_dir = Path(data_dir)
        self.roadmaps = self._load_roadmaps(data_dir / "roadmaps.csv")

    def _load_roadmaps(self, path: Path) -> Dict[str, List[dict]]:
        roadmaps: Dict[str, List[dict]] = {}
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                career = row["Career"]
                roadmaps.setdefault(career, []).append({
                    "step_order": int(row["Step Order"]),
                    "step": row["Step"],
                    "skill_targeted": row["Skill Targeted"],
                    "duration": row["Estimated Duration"],
                    "resource_type": row["Resource Type"],
                    "milestone": row["Milestone"].strip().lower() == "yes",
                })
        for career in roadmaps:
            roadmaps[career].sort(key=lambda s: s["step_order"])
        return roadmaps

    def build(self, career: str, skill_gaps: List[dict], top_gap_n: int = 5) -> List[dict]:
        """
        Returns the career's roadmap steps in their original prerequisite
        order, each annotated with is_priority: True if Skill Targeted
        matches one of the user's top_gap_n biggest skill gaps.
        """
        steps = self.roadmaps.get(career, [])
        priority_skills = {row["skill"] for row in skill_gaps[:top_gap_n] if row["gap"] > 0}

        annotated = []
        for step in steps:
            annotated.append({
                **step,
                "is_priority": step["skill_targeted"] in priority_skills,
            })
        return annotated

    def build_for_recommendations(self, recommendations: List[dict], top_gap_n: int = 5) -> List[dict]:
        """
        Takes Phase 7's output (recommendations already carrying
        skill_gaps) and attaches a roadmap to each career.
        """
        enriched = []
        for rec in recommendations:
            roadmap = self.build(rec["career"], rec.get("skill_gaps", []), top_gap_n=top_gap_n)
            enriched.append({**rec, "roadmap": roadmap})
        return enriched


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from feature_extraction import load_questions, extract_features
    from fuzzy_engine import FuzzyEngine
    from recommendation_engine import RecommendationEngine
    from skill_gap_analysis import SkillGapAnalyzer
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

    roadmap_builder = RoadmapBuilder(data_dir=str(data_dir))
    final = roadmap_builder.build_for_recommendations(enriched)

    top_pick = final[0]
    print(f"Roadmap for #1 pick: {top_pick['career']} ({top_pick['compatibility']}% match)\n")
    for step in top_pick["roadmap"]:
        flag = "[PRIORITY]" if step["is_priority"] else ""
        milestone = " [milestone]" if step["milestone"] else ""
        print(f"{step['step_order']}. {step['step']} ({step['duration']}, {step['resource_type']}){milestone} {flag}")
