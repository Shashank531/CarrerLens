"""
CareerLens — Concurrency Regression Test (FuzzyEngine)
======================================================
The Flask app runs under gunicorn with multiple threads, so several
assessments can be scored at the same time. skfuzzy's
ControlSystemSimulation mutates its own state on every compute(), which
means one simulation object must never be shared between threads.

Before the per-thread cache was introduced, two concurrent profiles
interleaved their sim.input writes and roughly half of the calls
returned the *other* profile's ranking — silently, with no exception.

Usage:
    python test_thread_safety.py
    pytest -q test_thread_safety.py
"""

import sys
import threading
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

from fuzzy_engine import FuzzyEngine  # noqa: E402

DATA = BACKEND.parent / "data" / "csv"

SKILLS = [
    "Programming", "Math", "Logical Thinking", "Problem Solving",
    "Attention to Detail", "Creativity", "Innovation", "Curiosity",
    "Research Interest", "Learning Ability", "Communication", "Leadership",
    "Empathy", "Teaching Ability", "Adaptability", "Discipline",
    "Decision Making", "Business Thinking", "Artistic Skill", "Physical Stamina",
]

# Two profiles that should rank completely differently.
PROFILE_A = {
    s: (9.5 if s in ("Programming", "Math", "Logical Thinking", "Problem Solving") else 1.0)
    for s in SKILLS
}
PROFILE_B = {
    s: (9.5 if s in ("Communication", "Leadership", "Empathy", "Teaching Ability") else 1.0)
    for s in SKILLS
}

THREADS = 4
ITERATIONS = 50


def test_score_all_is_thread_safe():
    engine = FuzzyEngine(data_dir=str(DATA))

    # Baselines, computed single-threaded before any concurrency starts.
    top_a = engine.score_all(PROFILE_A)[0]["career"]
    top_b = engine.score_all(PROFILE_B)[0]["career"]
    assert top_a != top_b, "test setup is invalid: both profiles rank the same career #1"

    mismatches = []
    lock = threading.Lock()

    def worker(profile, expected, label):
        for _ in range(ITERATIONS):
            got = engine.score_all(profile)[0]["career"]
            if got != expected:
                with lock:
                    mismatches.append((label, expected, got))

    threads = [
        threading.Thread(target=worker, args=(profile, expected, label))
        for profile, expected, label in (
            (PROFILE_A, top_a, "A"),
            (PROFILE_B, top_b, "B"),
            (PROFILE_A, top_a, "A"),
            (PROFILE_B, top_b, "B"),
        )
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    total = THREADS * ITERATIONS
    if mismatches:
        print(f"\n{len(mismatches)}/{total} concurrent calls returned the wrong top-1 career:")
        for label, expected, got in mismatches[:10]:
            print(f"  profile {label}: expected {expected!r}, got {got!r}")

    assert not mismatches, (
        f"{len(mismatches)}/{total} concurrent score_all() calls returned another "
        f"profile's ranking — ControlSystemSimulation is being shared across threads"
    )


if __name__ == "__main__":
    test_score_all_is_thread_safe()
    print("PASS: no cross-thread contamination observed")
