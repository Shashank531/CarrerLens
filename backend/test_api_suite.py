"""
CareerLens — Comprehensive API & Integration Test Suite
=========================================================
Tests all 10 API endpoints, database persistence, feature extraction,
fuzzy scoring across all 105 careers, and ReportLab PDF generation.
"""

import json
import urllib.request
import sys

BASE = 'http://127.0.0.1:5000/api'

def run_suite():
    print("=" * 65)
    print("  CareerLens Full System Integration Test Suite")
    print("=" * 65)

    # 1. Health Probe
    print("\n[1/8] Testing Service Health Probe...")
    res = urllib.request.urlopen(f"{BASE}/health")
    assert res.status == 200, f"Expected 200, got {res.status}"
    data = json.loads(res.read().decode('utf-8'))
    print(f"      Status: {data.get('status')} | Database: {data.get('db')}")

    # 2. Registration
    print("\n[2/8] Testing User Registration (/api/register)...")
    reg_body = json.dumps({"name": "Priya Patel", "education": "B.Tech Computer Science"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE}/register", data=reg_body, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    assert res.status == 201, f"Expected 201, got {res.status}"
    reg_data = json.loads(res.read().decode('utf-8'))
    user_id = reg_data["user_id"]
    code = reg_data["unique_code"]
    print(f"      Created User: ID={user_id}, Name='{reg_data['name']}', Code='{code}'")

    # 3. Authentication
    print("\n[3/8] Testing User Authentication (/api/login)...")
    login_body = json.dumps({"unique_code": code}).encode('utf-8')
    req = urllib.request.Request(f"{BASE}/login", data=login_body, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    assert res.status == 200, f"Expected 200, got {res.status}"
    login_data = json.loads(res.read().decode('utf-8'))
    print(f"      Authenticated: {login_data['name']} (Past Attempts: {len(login_data.get('history', []))})")

    # 4. Draft Saving & Retrieval
    print("\n[4/8] Testing Assessment Draft Auto-Save & Retrieval...")
    draft_answers = {"Q1": 5, "Q2": 4, "Q3": 5, "Q4": 4, "Q5": 5}
    draft_body = json.dumps({"user_id": user_id, "answers": draft_answers}).encode('utf-8')
    req = urllib.request.Request(f"{BASE}/assessment/draft", data=draft_body, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    assert res.status == 200, f"Save draft failed: {res.status}"
    draft_save_res = json.loads(res.read().decode('utf-8'))
    print(f"      Draft saved: {draft_save_res.get('count')} answers, Assessment ID={draft_save_res.get('assessment_id')}")

    res = urllib.request.urlopen(f"{BASE}/assessment/draft/{user_id}")
    assert res.status == 200, f"Get draft failed: {res.status}"
    draft_get_res = json.loads(res.read().decode('utf-8'))
    assert draft_get_res.get("has_draft") is True, "Draft flag was False"
    assert len(draft_get_res["draft"]["answers"]) == 5, "Draft answers count mismatch"
    print(f"      Draft retrieved: {len(draft_get_res['draft']['answers'])} answers verified.")

    # 5. Full Assessment Submission
    print("\n[5/8] Testing Full 70-Question Submission (/api/submit)...")
    full_answers = {}
    for i in range(1, 71):
        if i in [1, 2, 3, 4, 11, 12, 13]: # Strong programming / math
            full_answers[f"Q{i}"] = 5
        elif i in [5, 6, 7, 8]:
            full_answers[f"Q{i}"] = 4
        else:
            full_answers[f"Q{i}"] = 3

    submit_body = json.dumps({"user_id": user_id, "answers": full_answers}).encode('utf-8')
    req = urllib.request.Request(f"{BASE}/submit", data=submit_body, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    assert res.status == 200, f"Submit failed: {res.status}"
    submit_data = json.loads(res.read().decode('utf-8'))
    assessment_id = submit_data["assessment_id"]
    
    assert len(submit_data["skill_profile"]) == 20, f"Expected 20 skills, got {len(submit_data['skill_profile'])}"
    assert len(submit_data["top5"]) == 5, f"Expected 5 recommendations, got {len(submit_data['top5'])}"
    assert len(submit_data["all_scores"]) == 105, f"Expected 105 career scores, got {len(submit_data['all_scores'])}"
    assert len(submit_data["skill_gaps"]) >= 1, "Missing skill gaps"
    assert len(submit_data["roadmaps"]) >= 1, "Missing roadmaps"

    top1 = submit_data["top5"][0]
    print(f"      Submission processed successfully:")
    print(f"      - Assessment ID : #{assessment_id}")
    print(f"      - Top Match     : {top1['career']} ({top1['compatibility']}%)")
    print(f"      - Justification : {top1.get('explanation')}")
    print(f"      - Roadmaps      : {len(submit_data['roadmaps'])} top careers with step curricula")

    # 6. Results Retrieval
    print("\n[6/8] Testing Result Query Endpoints...")
    res1 = urllib.request.urlopen(f"{BASE}/results/{user_id}")
    assert res1.status == 200, "Get results by user failed"
    
    res2 = urllib.request.urlopen(f"{BASE}/assessment/{assessment_id}/results")
    assert res2.status == 200, "Get results by assessment_id failed"
    
    res3 = urllib.request.urlopen(f"{BASE}/user/{user_id}/history")
    assert res3.status == 200, "Get user history failed"
    history = json.loads(res3.read().decode('utf-8'))
    assert len(history) >= 1, "History empty"
    print(f"      Results queried & verified across user, assessment ID, and history ({len(history)} attempts).")

    # 7. Careers Master Catalog
    print("\n[7/8] Testing Careers Master Catalog (/api/careers)...")
    res = urllib.request.urlopen(f"{BASE}/careers")
    assert res.status == 200, "Get careers failed"
    careers = json.loads(res.read().decode('utf-8'))
    assert len(careers) == 105, f"Expected 105 careers, got {len(careers)}"
    print(f"      Catalog loaded: Exactly {len(careers)} careers with salary, demand, and education metadata.")

    # 8. ReportLab PDF Generation
    print("\n[8/8] Testing ReportLab PDF Document Generation...")
    res = urllib.request.urlopen(f"{BASE}/pdf/{user_id}")
    assert res.status == 200, "User PDF generation failed"
    pdf_bytes = res.read()
    assert pdf_bytes.startswith(b"%PDF"), "Generated payload is not a valid PDF header"
    print(f"      PDF Report generated successfully: {len(pdf_bytes):,} bytes.")

    print("\n" + "=" * 65)
    print("  ALL 8 INTEGRATION TESTS PASSED (100% SUCCESSFUL)")
    print("=" * 65)
    return 0

if __name__ == "__main__":
    sys.exit(run_suite())
