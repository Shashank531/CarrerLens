"""
CareerLens — Phase 4: Feature Extraction
==========================================
Converts raw assessment answers (1-5 Likert scale) into a normalized
0-10 skill profile across the 20 master skills.

Input:  {"Q1": 4, "Q2": 5, "Q3": 2, ...}   (question_id -> 1..5 rating)
Output: {"Programming": 8.5, "Math": 3.2, ...}  (skill -> 0..10 score)

Usage:
    from feature_extraction import extract_features, load_questions

    questions = load_questions("../data/csv/questions.csv")
    scores = extract_features(answers, questions)
"""

import csv
import statistics
from pathlib import Path
from typing import Dict, List


def load_questions(csv_path: str) -> List[dict]:
    """Load questions.csv into a list of dicts: id, module, text, skill."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            {
                "id": row["Question ID"],
                "module": row["Module"],
                "text": row["Question"],
                "skill": row["Mapped Skill"],
            }
            for row in reader
        ]


def extract_features(answers: Dict[str, int], questions: List[dict]) -> Dict[str, float]:
    """
    Group answers by their mapped skill, average them, and normalize
    from a 1-5 scale to a 0-10 scale.

    normalized = (raw_average - 1) / 4 * 10

    Any skill with zero answered questions is skipped (not scored),
    rather than silently defaulting to a mid-point — the caller should
    decide how to handle missing skills (e.g. flag incomplete profile).
    """
    skill_to_qids: Dict[str, List[str]] = {}
    for q in questions:
        skill_to_qids.setdefault(q["skill"], []).append(q["id"])

    scores: Dict[str, float] = {}
    for skill, qids in skill_to_qids.items():
        ratings = [answers[qid] for qid in qids if qid in answers and answers[qid] is not None]
        if not ratings:
            continue
        raw_avg = statistics.mean(ratings)
        normalized = round((raw_avg - 1) / 4 * 10, 2)
        scores[skill] = normalized

    return scores


def profile_completeness(answers: Dict[str, int], questions: List[dict]) -> float:
    """Fraction of the 70 questions actually answered (0.0 - 1.0)."""
    total = len(questions)
    answered = sum(1 for q in questions if q["id"] in answers and answers[q["id"]] is not None)
    return round(answered / total, 3) if total else 0.0


def skill_confidence(questions: List[dict]) -> Dict[str, int]:
    """
    How many questions back each skill. Skills backed by 1 question
    (e.g. Teaching Ability) are noisier than skills backed by 4+.
    Surface this alongside the profile so low-confidence skills can
    be flagged in the UI later if needed.
    """
    counts: Dict[str, int] = {}
    for q in questions:
        counts[q["skill"]] = counts.get(q["skill"], 0) + 1
    return counts


if __name__ == "__main__":
    # ---- Demo run with a fabricated answer set ----
    here = Path(__file__).parent
    questions_path = here.parent / "data" / "csv" / "questions.csv"
    questions = load_questions(str(questions_path))

    # Simulated answers: a "strong programmer" profile
    import random
    random.seed(7)
    demo_answers = {}
    for q in questions:
        if q["skill"] in ("Programming", "Logical Thinking", "Math", "Problem Solving"):
            demo_answers[q["id"]] = random.choice([4, 5, 5])
        else:
            demo_answers[q["id"]] = random.choice([2, 3, 3, 4])

    scores = extract_features(demo_answers, questions)
    completeness = profile_completeness(demo_answers, questions)
    confidence = skill_confidence(questions)

    print(f"Profile completeness: {completeness * 100:.0f}%\n")
    print(f"{'Skill':<22}{'Score /10':<12}{'# Questions'}")
    print("-" * 46)
    for skill, score in sorted(scores.items(), key=lambda kv: -kv[1]):
        print(f"{skill:<22}{score:<12}{confidence.get(skill, 0)}")
