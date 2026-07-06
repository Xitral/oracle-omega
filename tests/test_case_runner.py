from pathlib import Path

from src.oracle_omega.core.models import Decision
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario
from src.oracle_omega.reviewer import review

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "oracle" / "rules" / "starter_rules.yaml"
CASE_A = ROOT / "oracle" / "scenarios" / "example_path_pass.yaml"
CASE_B = ROOT / "oracle" / "scenarios" / "example_path_review.yaml"


def test_case_a_returns_allow():
    evidence = review(read_scenario(CASE_A), read_rule_file(ITEMS))

    assert evidence.decision == Decision.ALLOW
    assert all(item.passed for item in evidence.results)


def test_case_b_returns_review():
    evidence = review(read_scenario(CASE_B), read_rule_file(ITEMS))

    assert evidence.decision == Decision.REQUIRE_REVIEW
    assert sum(1 for item in evidence.results if not item.passed) == 2
