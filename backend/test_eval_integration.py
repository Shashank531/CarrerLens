import sys
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))
from app import app

def test_eval_endpoints():
    print("Testing Evaluation API endpoints with Flask test client...")
    client = app.test_client()

    # 1. Health
    res = client.get("/api/health")
    assert res.status_code == 200
    print("  [OK] /api/health:", res.get_json())

    # 2. Evaluation Datasets
    res = client.get("/api/evaluation/datasets")
    assert res.status_code == 200
    datasets_data = res.get_json()
    print("  [OK] /api/evaluation/datasets:", len(datasets_data.get("datasets", [])), "datasets found")

    # 3. Evaluation Results
    res = client.get("/api/evaluation/results")
    assert res.status_code == 200
    results_data = res.get_json()
    assert results_data["status"] == "success"
    assert "metrics" in results_data
    assert "top1_accuracy" in results_data["metrics"]
    assert "top5_accuracy" in results_data["metrics"]
    print("  [OK] /api/evaluation/results: Top-1 =", results_data["metrics"]["top1_accuracy"], "% | Top-5 =", results_data["metrics"]["top5_accuracy"], "%")

    # 4. Evaluation Page route
    res = client.get("/evaluation")
    assert res.status_code == 200
    assert b"CareerLens" in res.data
    assert b"Evaluation" in res.data
    print("  [OK] /evaluation: HTML dashboard served successfully (", len(res.data), "bytes )")

    print("\nALL EVALUATION INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_eval_endpoints()
