"""
CareerLens — Database Concurrency Test
======================================
The Flask app runs under gunicorn with several request threads, all sharing
one Database instance. Before the connection became thread-local, those
threads wrote through a single sqlite3 connection, so one request's commit()
could land in the middle of another request's transaction.

This test drives the Database API from concurrent threads and checks that
every write lands, no thread sees another thread's connection, and nothing
raises "database is locked".

Usage:
    python test_database_threads.py
    pytest -q test_database_threads.py
"""

import sys
import tempfile
import threading
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

from database import Database  # noqa: E402

THREADS = 8
USERS_PER_THREAD = 10


def test_concurrent_writers_do_not_interleave():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(str(Path(tmp) / "test.db"))
        db.init_schema()

        errors = []
        connections = []
        lock = threading.Lock()

        def worker(worker_id):
            try:
                for i in range(USERS_PER_THREAD):
                    user_id = db.create_user(
                        name=f"user-{worker_id}-{i}",
                        unique_code=f"U{worker_id}{i:03d}-0000",
                        education="B.Tech",
                    )
                    assessment_id = db.start_assessment(user_id)
                    db.save_responses(assessment_id, {"Q1": 4, "Q2": 5})
                    db.complete_assessment(assessment_id)
                    db.save_results(
                        assessment_id,
                        skill_profile={"Programming": 7.5},
                        top5=[{"career": "Software Engineer", "compatibility": 90.0}],
                    )
                with lock:
                    connections.append(id(db.connect()))
            except Exception as exc:  # noqa: BLE001 - surfaced in the assertion below
                with lock:
                    errors.append(f"worker {worker_id}: {exc!r}")

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, "concurrent writers raised: " + "; ".join(errors)

        # One connection object per thread, not one shared by all of them.
        assert len(set(connections)) == THREADS, (
            f"expected {THREADS} distinct connections, got {len(set(connections))}"
        )

        conn = db.connect()
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        results = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
        responses = conn.execute("SELECT COUNT(*) FROM responses").fetchone()[0]
        db.close()

        expected = THREADS * USERS_PER_THREAD
        assert users == expected, f"expected {expected} users, found {users}"
        assert results == expected, f"expected {expected} result rows, found {results}"
        assert responses == expected * 2, f"expected {expected * 2} responses, found {responses}"


if __name__ == "__main__":
    test_concurrent_writers_do_not_interleave()
    print("PASS: concurrent writes landed without interleaving")
