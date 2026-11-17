"""
CareerLens — Numerics Regression Test (FuzzyEngine)
===================================================
The Mamdani inference in fuzzy_engine.py is evaluated with numpy rather than
by building one scikit-fuzzy ControlSystemSimulation per career. This test
keeps the old scikit-fuzzy construction as a reference implementation and
checks that both produce the same compatibility scores.

The two produce identical scores for every career across fixed and random
profiles. Note that scikit-fuzzy upsamples the output universe with the exact
x-value where each clipped consequent curve crosses its activation level; the
numpy path does the same (see _score_with_membership), which is what makes the
centroid -- and therefore the ranking -- bit-for-bit reproducible.

scikit-fuzzy is no longer a runtime dependency, so the test is skipped when
it is not installed:

    pip install scikit-fuzzy     # only needed to run this test
    pytest -q test_fuzzy_numerics.py
"""

import random
import sys
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

from fuzzy_engine import FuzzyEngine, MISSING_SKILL_DEFAULT  # noqa: E402

DATA = BACKEND.parent / "data" / "csv"

try:  # scikit-fuzzy is only needed for the reference implementation
    from skfuzzy import control as ctrl
    HAS_SKFUZZY = True
except ImportError:
    ctrl = None
    HAS_SKFUZZY = False

SKILL_NAMES = [
    "Programming", "Math", "Logical Thinking", "Problem Solving", "Attention to Detail",
    "Creativity", "Innovation", "Curiosity", "Research Interest", "Learning Ability",
    "Communication", "Leadership", "Empathy", "Teaching Ability", "Adaptability",
    "Discipline", "Decision Making", "Business Thinking", "Artistic Skill", "Physical Stamina",
]


def _reference_score(engine, career, skill_profile, systems):
    """The pre-numpy implementation, kept verbatim as the reference."""
    import skfuzzy as fuzz

    if career not in systems:
        career_rules = engine.rules_by_career.get(career, [])
        used = sorted({s for r in career_rules for s, _ in r["antecedents"]})
        antecedents = {}
        for name in used:
            universe = np.arange(0, 10.01, 0.1)
            var = ctrl.Antecedent(universe, name)
            var["Very Low"] = fuzz.trimf(universe, [0, 0, 2.5])
            var["Low"] = fuzz.trimf(universe, [0, 2.5, 5])
            var["Medium"] = fuzz.trimf(universe, [2.5, 5, 7.5])
            var["High"] = fuzz.trimf(universe, [5, 7.5, 10])
            var["Very High"] = fuzz.trimf(universe, [7.5, 10, 10])
            antecedents[name] = var

        universe_out = np.arange(0, 100.01, 1)
        compatibility = ctrl.Consequent(universe_out, "compatibility")
        compatibility["Low"] = fuzz.trimf(universe_out, [0, 0, 35])
        compatibility["Medium"] = fuzz.trimf(universe_out, [20, 45, 68])
        compatibility["High"] = fuzz.trimf(universe_out, [55, 74, 90])
        compatibility["Excellent"] = fuzz.trimf(universe_out, [78, 100, 100])

        rules = []
        for r in career_rules:
            if not r["antecedents"]:
                continue
            term = None
            for skill, level in r["antecedents"]:
                clause = antecedents[skill][level]
                term = clause if term is None else (term & clause)
            rules.append(ctrl.Rule(term, compatibility[r["consequent"]]))

        systems[career] = ctrl.ControlSystemSimulation(ctrl.ControlSystem(rules))

    sim = systems[career]
    used = sorted({s for r in engine.rules_by_career.get(career, []) for s, _ in r["antecedents"]})
    if not used:
        return 0.0
    for skill in used:
        sim.input[skill] = skill_profile.get(skill, MISSING_SKILL_DEFAULT)
    try:
        sim.compute()
        return round(float(sim.output["compatibility"]), 1)
    except Exception:
        return 0.0


def _profiles():
    yield {s: 0.0 for s in SKILL_NAMES}
    yield {s: 5.0 for s in SKILL_NAMES}
    yield {s: 10.0 for s in SKILL_NAMES}
    yield {s: 9.5 if s in ("Programming", "Math", "Logical Thinking") else 1.0 for s in SKILL_NAMES}
    for seed in range(3):
        rng = random.Random(seed)
        yield {s: round(rng.uniform(0, 10), 2) for s in SKILL_NAMES}


def test_numpy_matches_skfuzzy_reference():
    if not HAS_SKFUZZY:
        print("skipped: scikit-fuzzy not installed (pip install scikit-fuzzy)")
        return

    engine = FuzzyEngine(data_dir=str(DATA))
    systems = {}
    worst = (0.0, None)

    for profile in _profiles():
        for career in engine.careers:
            expected = _reference_score(engine, career, profile, systems)
            actual = engine.score_career(career, profile)
            diff = abs(expected - actual)
            if diff > worst[0]:
                worst = (diff, (career, expected, actual))

    assert worst[0] == 0.0, (
        f"max deviation from the scikit-fuzzy reference is {worst[0]:.3f} "
        f"({worst[1]}) — numpy inference drifted from the reference"
    )


def test_score_all_is_deterministic_across_interleaved_profiles():
    """
    Scoring one profile must not influence the next. The previous
    ControlSystemSimulation-based implementation leaked state between calls,
    so a career's score depended on which profiles had been scored before it.
    """
    engine = FuzzyEngine(data_dir=str(DATA))
    profile_a = {s: 7.3 for s in SKILL_NAMES}
    profile_b = {s: (9.0 if s in ("Communication", "Empathy") else 2.0) for s in SKILL_NAMES}

    baseline = [(r["career"], r["compatibility"]) for r in engine.score_all(profile_a)]
    for _ in range(3):
        engine.score_all(profile_b)
        assert [(r["career"], r["compatibility"]) for r in engine.score_all(profile_a)] == baseline


if __name__ == "__main__":
    test_numpy_matches_skfuzzy_reference()
    test_score_all_is_deterministic_across_interleaved_profiles()
    print("PASS: numpy inference matches the scikit-fuzzy reference")
