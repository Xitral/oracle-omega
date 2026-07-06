from pathlib import Path

from src.oracle_omega.core.models import Decision
from src.oracle_omega.robustness_bundle import build_robustness_visualization_bundle
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "oracle" / "rules" / "starter_rules.yaml"
FRAGILE_CASE = ROOT / "oracle" / "scenarios" / "close_approach" / "fragile_corridor_pass.yaml"
REVIEW_CASE = ROOT / "oracle" / "scenarios" / "example_corridor_speed_review.yaml"


def test_robustness_bundle_includes_stress_replay_for_fragile_allowed_case():
    scenario = read_scenario(FRAGILE_CASE)
    rules = read_rule_file(ITEMS)

    bundle = build_robustness_visualization_bundle(scenario, rules, sample_override=20)

    assert bundle.scenario_id == "close-approach-fragile-corridor-pass"
    assert bundle.nominal_replay.decision == Decision.ALLOW
    assert bundle.robustness_report.monte_carlo.sample_count == 20
    assert bundle.robustness_report.adversarial_case.found is True
    assert bundle.stress_replay is not None
    assert bundle.stress_replay.decision == Decision.REQUIRE_REVIEW
    assert bundle.buffered_repair_replay is None


def test_robustness_bundle_includes_buffered_repair_replay_for_failing_case():
    scenario = read_scenario(REVIEW_CASE)
    rules = read_rule_file(ITEMS)

    bundle = build_robustness_visualization_bundle(
        scenario,
        rules,
        sample_override=20,
        compare_repair=True,
    )

    assert bundle.scenario_id == "example-corridor-speed-review"
    assert bundle.nominal_replay.decision == Decision.REQUIRE_REVIEW
    assert bundle.robustness_report.adversarial_case.found is False
    assert bundle.robustness_report.repair_comparison is not None
    assert bundle.robustness_report.repair_comparison.repaired_failure_probability == 0.0
    assert bundle.stress_replay is None
    assert bundle.buffered_repair_replay is not None
    assert bundle.buffered_repair_replay.decision == Decision.ALLOW
