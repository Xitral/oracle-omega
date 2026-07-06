from pathlib import Path

from src.oracle_omega.suite_runner import run_suite

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "oracle" / "rules" / "starter_rules.yaml"
SCENARIOS = ROOT / "oracle" / "scenarios"


def test_suite_runner_summarizes_existing_scenarios():
    summary = run_suite(SCENARIOS, ITEMS)

    assert summary.total_cases >= 3
    assert summary.valid_cases >= 3
    assert summary.invalid_cases == 0
    assert summary.decision_counts["ALLOW"] >= 1
    assert summary.decision_counts["REQUIRE_REVIEW"] >= 1
    assert summary.family_counts["close_approach"] >= 1
    assert summary.family_counts["surface_landing"] >= 1
    assert "PATH-SPEED-001" in summary.primary_rule_counts


def test_suite_runner_records_invalid_scenario_without_stopping(tmp_path):
    scenario = tmp_path / "invalid.yaml"
    scenario.write_text(
        "id: invalid\n"
        "name: Invalid\n"
        "family: close_approach\n"
        "planned_path: []\n",
        encoding="utf-8",
    )

    summary = run_suite(tmp_path, ITEMS)

    assert summary.total_cases == 1
    assert summary.valid_cases == 0
    assert summary.invalid_cases == 1
    assert summary.cases[0].valid is False
    assert "planned_path must contain" in summary.cases[0].error
