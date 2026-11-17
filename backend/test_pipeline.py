"""
CareerLens — Automated Validation Test Pipeline (test_pipeline.py)
===================================================================
Runs end-to-end automated validation tests across the feature extraction,
fuzzy inference engine, and recommendation engine for 5 predefined user profiles.

Profiles tested:
  1. Strong Programmer
  2. Creative Designer
  3. Strong Communicator / Leader
  4. Security Analyst
  5. All-Medium Profile (Robustness & Baseline Test)

Usage:
  python backend/test_pipeline.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

# Path setup so backend imports work regardless of current working directory
BASE = Path(__file__).parent
DATA = BASE.parent / "data" / "csv"

sys.path.insert(0, str(BASE))
from feature_extraction import load_questions, extract_features
from fuzzy_engine import FuzzyEngine
from recommendation_engine import RecommendationEngine


def generate_answers_for_profile(
    target_skills: Dict[str, float],
    questions: List[dict],
    default_score: float = 3.0
) -> Dict[str, int]:
    """
    Constructs a complete Likert 1-5 answer map that, when passed to extract_features(),
    reproduces the target skill scores (0-10) accurately across all questions.
    """
    skill_to_qids: Dict[str, List[str]] = {}
    for q in questions:
        skill_to_qids.setdefault(q["skill"], []).append(q["id"])

    answers: Dict[str, int] = {}
    for skill, qids in skill_to_qids.items():
        target = target_skills.get(skill, default_score)
        # Convert 0-10 normalized scale to 1-5 raw average: raw = 1 + (target / 10) * 4
        target_raw = 1.0 + (target / 10.0) * 4.0
        n = len(qids)

        # Distribute integer Likert responses (1 to 5) so the average matches target_raw
        total_sum = int(round(target_raw * n))
        total_sum = max(n * 1, min(n * 5, total_sum))

        base_val = total_sum // n
        remainder = total_sum % n

        for i, qid in enumerate(qids):
            val = base_val + (1 if i < remainder else 0)
            answers[qid] = max(1, min(5, val))

    return answers


def run_pipeline_tests():
    print("=" * 72)
    print("  CareerLens Automated Pipeline Validation Suite")
    print("=" * 72)
    print(f"Data directory: {DATA.resolve()}\n")

    # 1. Initialize Engines
    print("Initializing questions, FuzzyEngine, and RecommendationEngine...")
    questions = load_questions(str(DATA / "questions.csv"))
    fuzzy_engine = FuzzyEngine(data_dir=str(DATA))
    rec_engine = RecommendationEngine(data_dir=str(DATA))
    print(f"Loaded {len(questions)} questions across 20 skills.\n")

    # 2. Define 5 Test Profiles
    test_cases = [
        {
            "id": 1,
            "name": "Strong Programmer",
            "targets": {
                "Programming": 9.0,
                "Math": 9.0,
                "Problem Solving": 9.0,
                "Learning Ability": 8.0,
            },
            "default": 3.0,
            "expected_desc": "Technical / Software / AI roles (e.g. Software Engineer, AI/ML Engineer, Data Scientist)",
        },
        {
            "id": 2,
            "name": "Creative Designer",
            "targets": {
                "Creativity": 9.0,
                "Artistic Skill": 9.0,
                "Communication": 8.0,
                "Empathy": 7.0,
            },
            "default": 3.0,
            "expected_desc": "Design / Creative / Content roles (e.g. UI/UX Designer, Graphic Designer, Content Strategist)",
        },
        {
            "id": 3,
            "name": "Strong Communicator / Leader",
            "targets": {
                "Communication": 9.0,
                "Leadership": 9.0,
                "Empathy": 8.0,
                "Business Thinking": 8.0,
            },
            "default": 3.0,
            "expected_desc": "Management, Operations, Analysis, or Business roles",
        },
        {
            "id": 4,
            "name": "Security Analyst",
            "targets": {
                "Logical Thinking": 9.0,
                "Attention To Detail": 9.0,
                "Problem Solving": 8.0,
                "Programming": 7.0,
            },
            "default": 3.0,
            "expected_desc": "Security, Quality Assurance, Cloud Infrastructure, or System Analytics",
        },
        {
            "id": 5,
            "name": "All-Medium Profile (Robustness & Stability)",
            "targets": {},
            "default": 5.0,
            "expected_desc": "Balanced baseline profile; valid non-zero score between 0 and 100 with no exceptions",
        },
    ]

    passed_count = 0
    failed_count = 0

    # 3. Execute Tests
    for tc in test_cases:
        test_id = tc["id"]
        test_name = tc["name"]
        targets = tc["targets"]
        default_val = tc["default"]
        expected_desc = tc["expected_desc"]

        print("-" * 72)
        print(f"Test #{test_id}: {test_name}")
        print(f"Target Highlights : {targets if targets else 'All skills = 5.0'}")
        print(f"Expected Domain   : {expected_desc}")

        try:
            # Step A: Generate answers & extract features
            answers = generate_answers_for_profile(targets, questions, default_score=default_val)
            skill_profile = extract_features(answers, questions)

            # Step B: Score all careers via fuzzy inference engine
            ranked_careers = fuzzy_engine.score_all(skill_profile)

            # Step C: Generate top 5 recommendations with metadata and explanations
            top5 = rec_engine.recommend(skill_profile, ranked_careers, top_n=5)

            # Step D: Assertions
            assert top5 is not None, "Recommendation engine returned None"
            assert len(top5) == 5, f"Expected 5 recommendations, got {len(top5)}"

            top_career = top5[0]
            top_score = top_career.get("compatibility", 0.0)

            assert top_score > 0, f"Top compatibility must be > 0, got {top_score}"
            assert top_score <= 100, f"Top compatibility must be <= 100, got {top_score}"

            # Step E: Print Top 5 Results
            print("\n  Top 5 Recommendations:")
            for rank, c in enumerate(top5, start=1):
                cname = c.get("career", "Unknown")
                score = c.get("compatibility", 0.0)
                cat = c.get("category", "")
                sal = c.get("avg_salary_lpa", "")
                sal_str = f" | {sal} LPA" if sal else ""
                print(f"    {rank}. {cname:<28} : {score:>5.1f}% [{cat}{sal_str}]")

            # Print explanation for top match
            top_explanation = top_career.get("explanation", "")
            if top_explanation:
                print(f"  Explanation (#1): {top_explanation}")

            print(f"\n  [PASS] Test #{test_id} passed successfully.")
            passed_count += 1

        except Exception as e:
            print(f"\n  [FAIL] Test #{test_id} failed with error: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1

    # 4. Print Summary
    print("\n" + "=" * 72)
    print("  TEST SUITE SUMMARY")
    print("=" * 72)
    print(f"  Total Profiles Tested : {len(test_cases)}")
    print(f"  Passed                : {passed_count}")
    print(f"  Failed                : {failed_count}")
    print("=" * 72)

    if failed_count == 0:
        print("  ALL 5 PROFILE TESTS PASSED SUCCESSFULLY! (100% OK)\n")
        return 0
    else:
        print(f"  SOME TESTS FAILED ({failed_count} failures)\n")
        return 1


if __name__ == "__main__":
    exit_code = run_pipeline_tests()
    sys.exit(exit_code)
