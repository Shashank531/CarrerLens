"""
CareerLens — Evaluation & Accuracy Module (evaluate_recommendations.py)
========================================================================
Scientifically defensible evaluation pipeline for the CareerLens recommendation
system. Evaluates model recommendations against labelled ground truth datasets
using standard Information Retrieval (IR) and ranking metrics:

Metrics Computed:
  - Top-1 Accuracy (Exact Match at Rank 1)
  - Top-5 Accuracy / Hit Rate (Expected Career in Top 5)
  - Top-5 Flexible Hit Rate (Expected or Alternative Career in Top 5)
  - Category-Level Accuracy (Domain Alignment)
  - Top-5 Category Hit Rate
  - Mean Reciprocal Rank (MRR)
  - Rank Distribution Breakdown
  - Domain / Category Confusion & Performance Analysis

Usage:
  python evaluation/evaluate_recommendations.py
  python evaluation/evaluate_recommendations.py --dataset data/evaluation/ground_truth_demo.csv
"""

import sys
import os
import csv
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Path setup so backend imports work reliably
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BASE_DIR / "data" / "csv"
EVAL_DATA_DIR = BASE_DIR / "data" / "evaluation"
OUTPUT_DIR = BASE_DIR / "evaluation"

sys.path.insert(0, str(BACKEND_DIR))
from feature_extraction import load_questions, extract_features, skill_confidence
from fuzzy_engine import FuzzyEngine
from recommendation_engine import RecommendationEngine
from skill_gap_analysis import SkillGapAnalyzer
from roadmap_builder import RoadmapBuilder
from database import Database


SKILL_NAMES = [
    "Programming", "Math", "Logical Thinking", "Problem Solving", "Attention to Detail",
    "Creativity", "Innovation", "Curiosity", "Research Interest", "Learning Ability",
    "Communication", "Leadership", "Empathy", "Teaching Ability", "Adaptability",
    "Discipline", "Decision Making", "Business Thinking", "Artistic Skill", "Physical Stamina"
]


class RecommendationEvaluator:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.questions = load_questions(str(self.data_dir / "questions.csv"))
        self.fuzzy_engine = FuzzyEngine(data_dir=str(self.data_dir))
        self.rec_engine = RecommendationEngine(data_dir=str(self.data_dir))
        self.gap_analyzer = SkillGapAnalyzer(data_dir=str(self.data_dir))
        self.roadmap_builder = RoadmapBuilder(data_dir=str(self.data_dir))
        self.careers_meta = self._load_careers_meta()

    def _load_careers_meta(self) -> Dict[str, Dict[str, str]]:
        meta = {}
        careers_csv = self.data_dir / "careers.csv"
        if careers_csv.exists():
            with open(careers_csv, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    name = row.get("Career Name", "").strip()
                    meta[name] = {
                        "category": row.get("Category", "").strip(),
                        "salary": row.get("Avg Salary (LPA)", "").strip(),
                        "demand": row.get("Future Demand", "").strip(),
                        "difficulty": row.get("Difficulty", "").strip()
                    }
        return meta

    def load_dataset(self, file_path: Path) -> List[Dict[str, Any]]:
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset not found: {file_path}")

        records = []
        with open(file_path, newline="", encoding="utf-8") as f:
            lines = [l for l in f if not l.strip().startswith("#")]
            reader = csv.DictReader(lines)
            for row in reader:
                if not row or not row.get("student_id"):
                    continue

                student_id = row.get("student_id", "").strip()
                name = row.get("name", student_id).strip()
                expected_career = row.get("expected_career", "").strip()
                expected_category = row.get("expected_category", "").strip()
                
                # Multiple acceptable careers (pipe-separated)
                acceptable_raw = row.get("acceptable_careers", "")
                acceptable = [c.strip() for c in acceptable_raw.split("|") if c.strip()]
                if expected_career and expected_career not in acceptable:
                    acceptable.insert(0, expected_career)

                # Extract 20 skills if available directly in row
                skill_profile = {}
                for s in SKILL_NAMES:
                    val = row.get(s)
                    if val is None or val == "":
                        val = row.get(s.replace("to Detail", "To Detail"))
                    if val is None or val == "":
                        val = row.get(s.replace("To Detail", "to Detail"))
                    if val is not None and val != "":
                        try:
                            skill_profile[s] = float(val)
                        except ValueError:
                            skill_profile[s] = 5.0
                    else:
                        skill_profile[s] = 5.0

                records.append({
                    "student_id": student_id,
                    "name": name,
                    "expected_career": expected_career,
                    "expected_category": expected_category,
                    "acceptable_careers": acceptable,
                    "skill_profile": skill_profile,
                    "raw_row": row
                })
        return records

    def evaluate_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        skill_profile = case["skill_profile"]
        expected_career = case["expected_career"]
        expected_category = case["expected_category"]
        acceptable_careers = case["acceptable_careers"]

        # Run EXACT existing pipeline
        ranked_all = self.fuzzy_engine.score_all(skill_profile)
        top5 = self.rec_engine.recommend(skill_profile, ranked_all, top_n=5)

        # Ranked list of all 105 career names
        ranked_names = [r["career"] for r in ranked_all]
        top5_names = [r["career"] for r in top5]
        top1_name = top5_names[0] if top5_names else ""
        top1_meta = self.careers_meta.get(top1_name, {})
        top1_category = top1_meta.get("category", "")

        # Compute rank of primary expected career in 105 list (1-indexed)
        try:
            expected_rank = ranked_names.index(expected_career) + 1
        except ValueError:
            expected_rank = 999  # Not found

        # Compute best rank among acceptable careers
        acceptable_ranks = []
        for c in acceptable_careers:
            if c in ranked_names:
                acceptable_ranks.append(ranked_names.index(c) + 1)
        best_acceptable_rank = min(acceptable_ranks) if acceptable_ranks else 999

        # Metrics for this case
        is_top1 = (top1_name.lower() == expected_career.lower())
        is_top5 = (expected_rank <= 5)
        is_acceptable_top1 = any(c.lower() == top1_name.lower() for c in acceptable_careers)
        is_acceptable_top5 = any(c in top5_names for c in acceptable_careers)
        
        # Category matching
        is_category_match = (top1_category.lower() == expected_category.lower())
        top5_categories = [self.careers_meta.get(c, {}).get("category", "") for c in top5_names]
        is_top5_category_match = any(cat.lower() == expected_category.lower() for cat in top5_categories)

        # Reciprocal Rank (RR)
        reciprocal_rank = (1.0 / expected_rank) if expected_rank <= 105 else 0.0

        return {
            "student_id": case["student_id"],
            "name": case["name"],
            "expected_career": expected_career,
            "expected_category": expected_category,
            "acceptable_careers": acceptable_careers,
            "predicted_career": top1_name,
            "predicted_category": top1_category,
            "predicted_compatibility": top5[0]["compatibility"] if top5 else 0.0,
            "top5_careers": [
                {
                    "career": c["career"],
                    "compatibility": c["compatibility"],
                    "category": c.get("category", self.careers_meta.get(c["career"], {}).get("category", ""))
                }
                for c in top5
            ],
            "rank_of_expected": expected_rank,
            "best_acceptable_rank": best_acceptable_rank,
            "correct_top1": is_top1,
            "correct_top5": is_top5,
            "acceptable_top1": is_acceptable_top1,
            "acceptable_top5": is_acceptable_top5,
            "category_match": is_category_match,
            "top5_category_match": is_top5_category_match,
            "reciprocal_rank": round(reciprocal_rank, 4),
            "explanation": top5[0].get("explanation", "") if top5 else ""
        }

    def evaluate_all(self, dataset_path: Path) -> Dict[str, Any]:
        cases = self.load_dataset(dataset_path)
        is_synthetic = ("demo" in dataset_path.name.lower() or "synthetic" in dataset_path.name.lower())
        
        if not cases:
            return {
                "status": "empty",
                "message": "No valid ground truth records found in dataset.",
                "is_synthetic": is_synthetic,
                "dataset_file": dataset_path.name,
                "total_cases": 0,
                "top1_accuracy": 0.0,
                "top5_accuracy": 0.0,
                "category_accuracy": 0.0,
                "mrr": 0.0,
                "student_results": []
            }

        eval_results = [self.evaluate_case(c) for c in cases]
        n = len(eval_results)

        top1_correct = sum(1 for r in eval_results if r["correct_top1"])
        top5_correct = sum(1 for r in eval_results if r["correct_top5"])
        acceptable_top1_correct = sum(1 for r in eval_results if r["acceptable_top1"])
        acceptable_top5_correct = sum(1 for r in eval_results if r["acceptable_top5"])
        category_correct = sum(1 for r in eval_results if r["category_match"])
        top5_category_correct = sum(1 for r in eval_results if r["top5_category_match"])
        mrr_sum = sum(r["reciprocal_rank"] for r in eval_results)
        ranks_sum = sum(min(r["rank_of_expected"], 105) for r in eval_results)

        # Rank distribution
        rank_dist = {
            "rank_1": sum(1 for r in eval_results if r["rank_of_expected"] == 1),
            "rank_2_to_3": sum(1 for r in eval_results if 2 <= r["rank_of_expected"] <= 3),
            "rank_4_to_5": sum(1 for r in eval_results if 4 <= r["rank_of_expected"] <= 5),
            "rank_6_to_10": sum(1 for r in eval_results if 6 <= r["rank_of_expected"] <= 10),
            "rank_gt_10": sum(1 for r in eval_results if r["rank_of_expected"] > 10),
        }

        # Category performance breakdown
        categories = sorted(list(set(r["expected_category"] for r in eval_results if r["expected_category"])))
        cat_breakdown = {}
        for cat in categories:
            cat_cases = [r for r in eval_results if r["expected_category"] == cat]
            c_n = len(cat_cases)
            c_top1 = sum(1 for r in cat_cases if r["correct_top1"])
            c_top5 = sum(1 for r in cat_cases if r["correct_top5"])
            c_cat_match = sum(1 for r in cat_cases if r["category_match"])
            cat_breakdown[cat] = {
                "total_cases": c_n,
                "top1_correct": c_top1,
                "top1_accuracy": round((c_top1 / c_n) * 100, 1),
                "top5_correct": c_top5,
                "top5_accuracy": round((c_top5 / c_n) * 100, 1),
                "category_accuracy": round((c_cat_match / c_n) * 100, 1),
            }

        summary = {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset_file": dataset_path.name,
            "is_synthetic": is_synthetic,
            "disclaimer": (
                "SYNTHETIC DEMONSTRATION DATA — NOT REAL-WORLD ACCURACY"
                if is_synthetic else
                "EMPIRICAL DATASET EVALUATION"
            ),
            "total_cases": n,
            "metrics": {
                "top1_correct": top1_correct,
                "top1_accuracy": round((top1_correct / n) * 100, 2),
                "top5_correct": top5_correct,
                "top5_accuracy": round((top5_correct / n) * 100, 2),
                "acceptable_top1_correct": acceptable_top1_correct,
                "acceptable_top1_accuracy": round((acceptable_top1_correct / n) * 100, 2),
                "acceptable_top5_correct": acceptable_top5_correct,
                "acceptable_top5_accuracy": round((acceptable_top5_correct / n) * 100, 2),
                "category_correct": category_correct,
                "category_accuracy": round((category_correct / n) * 100, 2),
                "top5_category_correct": top5_category_correct,
                "top5_category_accuracy": round((top5_category_correct / n) * 100, 2),
                "mrr": round(mrr_sum / n, 4),
                "mean_expected_rank": round(ranks_sum / n, 2)
            },
            "rank_distribution": rank_dist,
            "category_breakdown": cat_breakdown,
            "student_results": eval_results
        }
        return summary


def save_results(results: Dict[str, Any], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Save JSON
    json_path = output_dir / "results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # 2. Save CSV
    csv_path = output_dir / "results.csv"
    students = results.get("student_results", [])
    if students:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "student_id", "name", "expected_career", "expected_category",
                "predicted_career", "predicted_category", "predicted_compatibility",
                "rank_of_expected", "correct_top1", "correct_top5",
                "acceptable_top5", "category_match", "reciprocal_rank",
                "top5_recommendations"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in students:
                top5_str = " | ".join([f"{c['career']} ({c['compatibility']}%)" for c in s.get("top5_careers", [])])
                writer.writerow({
                    "student_id": s["student_id"],
                    "name": s["name"],
                    "expected_career": s["expected_career"],
                    "expected_category": s["expected_category"],
                    "predicted_career": s["predicted_career"],
                    "predicted_category": s["predicted_category"],
                    "predicted_compatibility": s.get("predicted_compatibility", 0.0),
                    "rank_of_expected": s["rank_of_expected"],
                    "correct_top1": s["correct_top1"],
                    "correct_top5": s["correct_top5"],
                    "acceptable_top5": s.get("acceptable_top5", False),
                    "category_match": s["category_match"],
                    "reciprocal_rank": s["reciprocal_rank"],
                    "top5_recommendations": top5_str
                })

    print(f"\n[OK] Results saved to:")
    print(f"     - JSON: {json_path}")
    print(f"     - CSV : {csv_path}")


def print_cli_report(results: Dict[str, Any]):
    m = results["metrics"]
    print("\n" + "=" * 78)
    print("  CAREERLENS RECOMMENDATION SYSTEM — EVALUATION REPORT")
    print("=" * 78)
    if results["is_synthetic"]:
        print("  [! NOTICE !] " + results["disclaimer"])
        print("  Real-world recommendation accuracy has not yet been established.")
        print("  This benchmark uses a synthetic test cohort to test evaluation metrics.")
    else:
        print("  [DATASET] " + results["dataset_file"])
    print("-" * 78)
    print(f"  Total Labelled Test Cases    : {results['total_cases']}")
    print(f"  Top-1 Accuracy (Exact Match) : {m['top1_accuracy']}%  ({m['top1_correct']}/{results['total_cases']})")
    print(f"  Top-5 Accuracy (Hit Rate)    : {m['top5_accuracy']}%  ({m['top5_correct']}/{results['total_cases']})")
    print(f"  Top-5 Flexible Hit Rate      : {m['acceptable_top5_accuracy']}%  ({m['acceptable_top5_correct']}/{results['total_cases']})")
    print(f"  Category-Level Accuracy      : {m['category_accuracy']}%  ({m['category_correct']}/{results['total_cases']})")
    print(f"  Top-5 Category Hit Rate      : {m['top5_category_accuracy']}%  ({m['top5_category_correct']}/{results['total_cases']})")
    print(f"  Mean Reciprocal Rank (MRR)   : {m['mrr']}")
    print(f"  Average Rank of Expected Job : #{m['mean_expected_rank']} (out of 105 careers)")
    print("-" * 78)
    print("  Expected Career Rank Distribution:")
    rd = results["rank_distribution"]
    print(f"    - Rank 1 (Top Pick)        : {rd['rank_1']:2d} ({rd['rank_1']/results['total_cases']*100:.1f}%)")
    print(f"    - Rank 2 to 3              : {rd['rank_2_to_3']:2d} ({rd['rank_2_to_3']/results['total_cases']*100:.1f}%)")
    print(f"    - Rank 4 to 5              : {rd['rank_4_to_5']:2d} ({rd['rank_4_to_5']/results['total_cases']*100:.1f}%)")
    print(f"    - Rank 6 to 10             : {rd['rank_6_to_10']:2d} ({rd['rank_6_to_10']/results['total_cases']*100:.1f}%)")
    print(f"    - Rank > 10                : {rd['rank_gt_10']:2d} ({rd['rank_gt_10']/results['total_cases']*100:.1f}%)")
    print("-" * 78)
    print("  Category Performance Breakdown:")
    print(f"    {'Category':<16} {'Cases':<8} {'Top-1 Acc':<12} {'Top-5 Acc':<12} {'Domain Acc'}")
    for cat, c_info in results["category_breakdown"].items():
        print(f"    {cat:<16} {c_info['total_cases']:<8} {c_info['top1_accuracy']:>5.1f}%      {c_info['top5_accuracy']:>5.1f}%      {c_info['category_accuracy']:>5.1f}%")
    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(description="CareerLens Recommendation Evaluation Suite")
    parser.add_argument("--dataset", type=str, default=None, help="Path to ground truth CSV dataset")
    parser.add_argument("--outdir", type=str, default=str(OUTPUT_DIR), help="Output directory for results")
    args = parser.parse_args()

    # Determine dataset path: check custom path -> ground_truth.csv (if has data) -> ground_truth_demo.csv
    if args.dataset:
        dataset_path = Path(args.dataset)
    else:
        real_path = EVAL_DATA_DIR / "ground_truth.csv"
        demo_path = EVAL_DATA_DIR / "ground_truth_demo.csv"
        # Check if real_path exists and has rows other than header/comments
        has_real_data = False
        if real_path.exists():
            with open(real_path, "r", encoding="utf-8") as f:
                data_lines = [l for l in f if l.strip() and not l.startswith("#")]
                if len(data_lines) > 1:
                    has_real_data = True
        dataset_path = real_path if has_real_data else demo_path

    print(f"Initializing CareerLens Evaluator...")
    print(f"Using dataset: {dataset_path}")

    evaluator = RecommendationEvaluator()
    results = evaluator.evaluate_all(dataset_path)
    save_results(results, Path(args.outdir))
    print_cli_report(results)


if __name__ == "__main__":
    main()
