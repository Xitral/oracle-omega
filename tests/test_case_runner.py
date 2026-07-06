from pathlib import Path

from src.oracle_omega.core.models import Decision
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario
from src.oracle_omega.reviewer import review

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "oracle" / "rules" / "starter_rules.yaml"
CASE_A = ROOT / "oracle" / "scenarios" / "example_path_pass.yaml"
CASE_B = ROOT / "oracle" / "scenarios" / "example_path_review.yaml"
CASE_C = ROOT / "oracle" / "scenarios" / "example_corridor_speed_review.yaml"


def result_ids(evidence):
    return {item.rule_id for item in evidence.results}


def failed_ids(evidence):
    return {item.rule_id for item in evidence.results if not item.passed}


def test_close_approach_pass_uses_close_approach_checks():
    evidence = review(read_scenario(CASE_A), read_rule_file(ITEMS))

    assert evidence.decision == Decision.ALLOW
    assert result_ids(evidence) == {
        "APPROACH-CLEARANCE-001",
        "PATH-CORRIDOR-001",
        "PATH-SPEED-001",
    }
    assert all(item.passed for item in evidence.results)


def test_surface_landing_review_uses_surface_checks():
    evidence = review(read_scenario(CASE_B), read_rule_file(ITEMS))

    assert evidence.decision == Decision.REQUIRE_REVIEW
    assert result_ids(evidence) == {
        "APPROACH-CLEARANCE-001",
        "LANDING-TILT-001",
        "PATH-SPEED-001",
    }
    assert failed_ids(evidence) == {"APPROACH-CLEARANCE-001", "LANDING-TILT-001"}


def test_close_approach_review_flags_corridor_and_speed():
    evidence = review(read_scenario(CASE_C), read_rule_file(ITEMS))

    assert evidence.decision == Decision.REQUIRE_REVIEW
    assert result_ids(evidence) == {
        "APPROACH-CLEARANCE-001",
        "PATH-CORRIDOR-001",
        "PATH-SPEED-001",
    }
    assert failed_ids(evidence) == {"PATH-CORRIDOR-001", "PATH-SPEED-001"}
