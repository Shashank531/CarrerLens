"""
CareerLens — User Data CSV Exporter
===================================
Exports all user data, assessment attempts, completion statuses,
and latest career recommendation results into CSV files in the data/ folder.
"""

import sqlite3
import json
import csv
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "data"


def export_userdata_to_csv(db_path: Optional[str] = None):
    """
    Reads users, assessments, responses, and results from SQLite
    and exports formatted CSV files to:
      - data/userdata/userdata.csv
      - data/userdata/user_attempts.csv
      - data/csv/userdata.csv
      - data/userdata.csv
    """
    if db_path is None:
        db_path = str(BASE_DIR / "careerlens.db")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Ensure destination directories exist
    userdata_dir = DATA_DIR / "userdata"
    userdata_dir.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "csv").mkdir(parents=True, exist_ok=True)

    users = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()

    userdata_rows = []
    attempts_rows = []

    for u in users:
        uid = u["id"]
        uname = u["name"]
        ucode = u["unique_code"]
        uedu = u["education"] or ""
        ucreated = u["created_at"]

        # Fetch all assessments for this user
        assessments = conn.execute(
            """
            SELECT a.*, r.top5_json,
                   (SELECT COUNT(*) FROM responses res WHERE res.assessment_id = a.id) as response_count
            FROM assessments a
            LEFT JOIN results r ON r.assessment_id = a.id
            WHERE a.user_id = ?
            ORDER BY a.id ASC
            """,
            (uid,),
        ).fetchall()

        total_attempts = len(assessments)
        completed_attempts = sum(1 for a in assessments if a["status"] == "completed")
        in_progress_attempts = total_attempts - completed_attempts

        last_attempt_id = assessments[-1]["id"] if assessments else ""
        last_attempt_date = (
            (assessments[-1]["completed_at"] or assessments[-1]["started_at"])
            if assessments
            else ""
        )
        last_attempt_status = assessments[-1]["status"] if assessments else "no_attempts"

        latest_top_career = ""
        latest_top_score = ""
        latest_top_3 = ""
        latest_top_5 = ""

        # Process each attempt
        for a in assessments:
            top5 = []
            if a["top5_json"]:
                try:
                    top5 = json.loads(a["top5_json"])
                except Exception:
                    top5 = []

            c1 = top5[0].get("career", "") if len(top5) > 0 else ""
            s1 = round(top5[0].get("compatibility", top5[0].get("score", 0)), 1) if len(top5) > 0 else ""
            c2 = top5[1].get("career", "") if len(top5) > 1 else ""
            s2 = round(top5[1].get("compatibility", top5[1].get("score", 0)), 1) if len(top5) > 1 else ""
            c3 = top5[2].get("career", "") if len(top5) > 2 else ""
            s3 = round(top5[2].get("compatibility", top5[2].get("score", 0)), 1) if len(top5) > 2 else ""
            c4 = top5[3].get("career", "") if len(top5) > 3 else ""
            c5 = top5[4].get("career", "") if len(top5) > 4 else ""

            attempts_rows.append({
                "assessment_id": a["id"],
                "user_id": uid,
                "unique_code": ucode,
                "user_name": uname,
                "education": uedu,
                "started_at": a["started_at"],
                "completed_at": a["completed_at"] or "",
                "status": a["status"],
                "responses_count": a["response_count"],
                "top_career_1": c1,
                "top_career_1_score": s1,
                "top_career_2": c2,
                "top_career_2_score": s2,
                "top_career_3": c3,
                "top_career_3_score": s3,
                "top_career_4": c4,
                "top_career_5": c5,
            })

        # Latest assessment with results for user summary
        completed_with_results = [a for a in assessments if a["top5_json"]]
        if completed_with_results:
            latest = completed_with_results[-1]
            try:
                top5 = json.loads(latest["top5_json"])
                if top5:
                    latest_top_career = top5[0].get("career", "")
                    latest_top_score = round(
                        top5[0].get("compatibility", top5[0].get("score", 0)), 1
                    )
                    latest_top_3 = "; ".join(
                        [c.get("career", "") for c in top5[:3] if c.get("career")]
                    )
                    latest_top_5 = "; ".join(
                        [c.get("career", "") for c in top5[:5] if c.get("career")]
                    )
            except Exception:
                pass

        attempt_ids = ", ".join(str(a["id"]) for a in assessments)

        userdata_rows.append({
            "user_id": uid,
            "unique_code": ucode,
            "name": uname,
            "education": uedu,
            "registered_at": ucreated,
            "total_attempts": total_attempts,
            "completed_attempts": completed_attempts,
            "in_progress_attempts": in_progress_attempts,
            "last_attempt_id": last_attempt_id,
            "last_attempt_date": last_attempt_date,
            "last_attempt_status": last_attempt_status,
            "latest_top_career": latest_top_career,
            "latest_compatibility_score": latest_top_score,
            "latest_top_3_careers": latest_top_3,
            "latest_top_5_careers": latest_top_5,
            "all_assessment_ids": attempt_ids,
        })

    conn.close()

    # Userdata fieldnames
    user_fields = [
        "user_id",
        "unique_code",
        "name",
        "education",
        "registered_at",
        "total_attempts",
        "completed_attempts",
        "in_progress_attempts",
        "last_attempt_id",
        "last_attempt_date",
        "last_attempt_status",
        "latest_top_career",
        "latest_compatibility_score",
        "latest_top_3_careers",
        "latest_top_5_careers",
        "all_assessment_ids",
    ]

    # Attempts fieldnames
    attempt_fields = [
        "assessment_id",
        "user_id",
        "unique_code",
        "user_name",
        "education",
        "started_at",
        "completed_at",
        "status",
        "responses_count",
        "top_career_1",
        "top_career_1_score",
        "top_career_2",
        "top_career_2_score",
        "top_career_3",
        "top_career_3_score",
        "top_career_4",
        "top_career_5",
    ]

    # Write userdata.csv to multiple convenient locations
    target_files = [
        userdata_dir / "userdata.csv",
        DATA_DIR / "csv" / "userdata.csv",
        DATA_DIR / "userdata.csv",
    ]

    for file_path in target_files:
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=user_fields)
            writer.writeheader()
            writer.writerows(userdata_rows)

    # Write granular user_attempts.csv
    attempts_target_files = [
        userdata_dir / "user_attempts.csv",
        DATA_DIR / "csv" / "user_attempts.csv",
    ]
    for file_path in attempts_target_files:
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=attempt_fields)
            writer.writeheader()
            writer.writerows(attempts_rows)

    return {
        "users_count": len(userdata_rows),
        "attempts_count": len(attempts_rows),
        "exported_files": [str(p) for p in target_files + attempts_target_files],
    }


if __name__ == "__main__":
    res = export_userdata_to_csv()
    print(f"Successfully exported {res['users_count']} users and {res['attempts_count']} attempts.")
    for p in res["exported_files"]:
        print(f"  -> {p}")
