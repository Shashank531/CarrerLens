"""
CareerLens — Phase 9: Database Development (updated)
=====================================================
Added:
  - unique_code column on users  (e.g. "ARJUN-4827")
  - get_user_by_code()           — used by login route
  - create_user() now accepts unique_code

Everything else is unchanged from the original phase-9 file.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    unique_code TEXT    UNIQUE NOT NULL,
    education   TEXT,
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS assessments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    started_at   TEXT    NOT NULL,
    completed_at TEXT,
    status       TEXT    NOT NULL DEFAULT 'in_progress',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS responses (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id  INTEGER NOT NULL,
    question_id    TEXT    NOT NULL,
    answer_value   INTEGER NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id),
    UNIQUE (assessment_id, question_id)
);

CREATE TABLE IF NOT EXISTS results (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id       INTEGER NOT NULL UNIQUE,
    skill_profile_json  TEXT    NOT NULL,
    top5_json           TEXT    NOT NULL,
    top30_json          TEXT,
    skill_gaps_json     TEXT,
    roadmaps_json       TEXT,
    created_at          TEXT    NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, db_path: str = "careerlens.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA synchronous = NORMAL")
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def init_schema(self):
        conn = self.connect()
        conn.executescript(SCHEMA)
        # Migrate existing results table if columns are missing
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(results)")
        columns = [col[1] for col in cursor.fetchall()]
        if columns:
            if "top30_json" not in columns:
                cursor.execute("ALTER TABLE results ADD COLUMN top30_json TEXT")
            if "skill_gaps_json" not in columns:
                cursor.execute("ALTER TABLE results ADD COLUMN skill_gaps_json TEXT")
            if "roadmaps_json" not in columns:
                cursor.execute("ALTER TABLE results ADD COLUMN roadmaps_json TEXT")
        conn.commit()

    # ── Users ────────────────────────────────────────────────────

    def create_user(
        self,
        name: str,
        unique_code: str,
        education: str = None,
    ) -> int:
        conn = self.connect()
        cur = conn.execute(
            "INSERT INTO users (name, unique_code, education, created_at) VALUES (?, ?, ?, ?)",
            (name, unique_code, education, _now()),
        )
        conn.commit()
        return cur.lastrowid

    def get_user_by_code(self, unique_code: str) -> Optional[dict]:
        conn = self.connect()
        row = conn.execute(
            "SELECT * FROM users WHERE unique_code = ?", (unique_code,)
        ).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        conn = self.connect()
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── Assessments ──────────────────────────────────────────────

    def start_assessment(self, user_id: int) -> int:
        conn = self.connect()
        cur = conn.execute(
            "INSERT INTO assessments (user_id, started_at, status) VALUES (?, ?, 'in_progress')",
            (user_id, _now()),
        )
        conn.commit()
        return cur.lastrowid

    def complete_assessment(self, assessment_id: int):
        conn = self.connect()
        conn.execute(
            "UPDATE assessments SET completed_at = ?, status = 'completed' WHERE id = ?",
            (_now(), assessment_id),
        )
        conn.commit()

    # ── Responses ────────────────────────────────────────────────

    def save_responses(self, assessment_id: int, answers: Dict[str, int]):
        conn = self.connect()
        conn.executemany(
            """INSERT INTO responses (assessment_id, question_id, answer_value)
               VALUES (?, ?, ?)
               ON CONFLICT(assessment_id, question_id) DO UPDATE SET answer_value = excluded.answer_value""",
            [(assessment_id, qid, val) for qid, val in answers.items()],
        )
        conn.commit()

    def get_responses(self, assessment_id: int) -> Dict[str, int]:
        conn = self.connect()
        rows = conn.execute(
            "SELECT question_id, answer_value FROM responses WHERE assessment_id = ?",
            (assessment_id,),
        ).fetchall()
        return {row["question_id"]: row["answer_value"] for row in rows}

    # ── Results ──────────────────────────────────────────────────

    def _format_result_row(self, row: sqlite3.Row) -> dict:
        keys = row.keys()
        res = {
            "assessment_id": row["assessment_id"],
            "skill_profile": json.loads(row["skill_profile_json"]),
            "top5":          json.loads(row["top5_json"]),
            "created_at":    row["created_at"],
        }
        if "top30_json" in keys and row["top30_json"]:
            try:
                res["top30"] = json.loads(row["top30_json"])
            except Exception:
                res["top30"] = None
        else:
            res["top30"] = None

        if "skill_gaps_json" in keys and row["skill_gaps_json"]:
            try:
                res["skill_gaps"] = json.loads(row["skill_gaps_json"])
            except Exception:
                res["skill_gaps"] = None
        else:
            res["skill_gaps"] = None

        if "roadmaps_json" in keys and row["roadmaps_json"]:
            try:
                res["roadmaps"] = json.loads(row["roadmaps_json"])
            except Exception:
                res["roadmaps"] = None
        else:
            res["roadmaps"] = None

        return res

    def save_results(
        self,
        assessment_id: int,
        skill_profile: Dict[str, float],
        top5: List[dict],
        top30: Optional[List[dict]] = None,
        skill_gaps: Optional[dict] = None,
        roadmaps: Optional[dict] = None,
    ):
        conn = self.connect()
        conn.execute(
            """INSERT INTO results (assessment_id, skill_profile_json, top5_json, top30_json, skill_gaps_json, roadmaps_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(assessment_id) DO UPDATE SET
                 skill_profile_json = excluded.skill_profile_json,
                 top5_json          = excluded.top5_json,
                 top30_json         = excluded.top30_json,
                 skill_gaps_json    = excluded.skill_gaps_json,
                 roadmaps_json      = excluded.roadmaps_json,
                 created_at         = excluded.created_at""",
            (
                assessment_id,
                json.dumps(skill_profile),
                json.dumps(top5),
                json.dumps(top30) if top30 is not None else None,
                json.dumps(skill_gaps) if skill_gaps is not None else None,
                json.dumps(roadmaps) if roadmaps is not None else None,
                _now(),
            ),
        )
        conn.commit()

    def get_results(self, assessment_id: int) -> Optional[dict]:
        conn = self.connect()
        row = conn.execute(
            "SELECT * FROM results WHERE assessment_id = ?", (assessment_id,)
        ).fetchone()
        if not row:
            return None
        return self._format_result_row(row)

    # ── History / Dashboard ──────────────────────────────────────

    def get_user_history(self, user_id: int) -> List[dict]:
        conn = self.connect()
        rows = conn.execute(
            """SELECT a.id as assessment_id, a.started_at, a.completed_at, a.status,
                      r.created_at as result_created_at, r.top5_json
               FROM assessments a
               LEFT JOIN results r ON r.assessment_id = a.id
               WHERE a.user_id = ?
               ORDER BY a.id DESC""",
            (user_id,),
        ).fetchall()
        history = []
        for r in rows:
            top_careers = []
            top_compat = 0
            if r["top5_json"]:
                try:
                    t5 = json.loads(r["top5_json"])
                    top_careers = [c.get("career") for c in t5[:3] if c.get("career")]
                    if t5 and len(t5) > 0:
                        top_compat = round(t5[0].get("compatibility", t5[0].get("score", 0)), 1)
                except Exception:
                    pass
            history.append({
                "assessment_id": r["assessment_id"],
                "started_at": r["started_at"],
                "completed_at": r["completed_at"],
                "created_at": r["result_created_at"] or r["completed_at"] or r["started_at"],
                "status": r["status"],
                "has_results": bool(r["top5_json"]),
                "top_careers": top_careers,
                "top_compatibility": top_compat,
            })
        return history

    def get_latest_result(self, user_id: int) -> Optional[dict]:
        conn = self.connect()
        row = conn.execute(
            """SELECT r.* FROM results r
               JOIN assessments a ON a.id = r.assessment_id
               WHERE a.user_id = ? ORDER BY a.id DESC LIMIT 1""",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return self._format_result_row(row)

    # ── Draft Management ─────────────────────────────────────────

    def save_draft(self, user_id: int, answers: Dict[str, int]) -> int:
        """Saves in-progress assessment draft responses for a user."""
        conn = self.connect()
        # Find active in_progress assessment or create new one
        row = conn.execute(
            "SELECT id FROM assessments WHERE user_id = ? AND status = 'in_progress' ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        if row:
            assessment_id = row["id"]
        else:
            assessment_id = self.start_assessment(user_id)

        self.save_responses(assessment_id, answers)
        return assessment_id

    def get_draft(self, user_id: int) -> Optional[dict]:
        """Retrieves active in-progress assessment responses for a user."""
        conn = self.connect()
        row = conn.execute(
            "SELECT id, started_at FROM assessments WHERE user_id = ? AND status = 'in_progress' ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        assessment_id = row["id"]
        answers = self.get_responses(assessment_id)
        return {
            "assessment_id": assessment_id,
            "started_at": row["started_at"],
            "answers": answers,
            "count": len(answers),
        }

