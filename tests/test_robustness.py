from pathlib import Path

from src.oracle_omega.core.models import Decision
from src.oracle_omega.robustness import (
    build_robustness_report,
    find_worst_case_stress,
    run_monte_carlo,
    uncertainty_from_scenario,
)
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "oracle" / "rules" / "starter_rules.yaml"
PASS_CASE = ROOT / "oracle" / "scenarios" / "example_path_pass.yaml"
FRAGILE_CASE = ROOT / "oracle" / "scenarios" / "close_approach" / "fragile_corridor_pass.yaml"
REVIEW_CASE = ROOT / "oracle" / "scenarios" / "example_corridor_speed_review.yaml"


def test_uncertainty_config_reads_scenario_parameters():
    scenario = read_scenario(PASS_CASE)
    config = uncertainty_from_scenario(scenario, sample_override=12)

    assert config.samples == 12
    assert config.position_sigma.y == 0.2
    assert config.timing_sigma == 0.15
    assert config.seed == 11


def test_monte_carlo_summary_counts_all_samples():
    scenario = read_scenario(PASS_CASE)
    rules = read_rule_file(ITEMS)
    config = uncertainty_from_scenario(scenario, sample_override=20)

    summary = run_monte_carlo(scenario, rules, config)

    assert summary.sample_count == 20
    assert summary.pass_count + summary.fail_count == 20
    assert 0.0 <= summary.failure_probability <= 1.0
    assert sum(summary.decision_counts.values()) == 20


def test_fragile_nominal_case_has_nonzero_uncertainty_risk():
    scenario = read_scenario(FRAGILE_CASE)
    rules = read_rule_file(ITEMS)

    report = build_robustness_report(scenario, rules, sample_override=40)

    assert report.nominal_decision == Decision.ALLOW
    assert report.monte_carlo.fail_count > 0
    assert report.monte_carlo.failure_probability > 0.0
    assert report.monte_carlo.most_common_failure == "PATH-CORRIDOR-001"


def test_worst_case_stress_search_can_find_failure_for_allowed_path():
    scenario = read_scenario(PASS_CASE)
    rules = read_rule_file(ITEMS)

    result = find_worst_case_stress(scenario, rules, max_magnitude=3.0, steps=60)

    assert result.found is True
    assert result.triggered_rule is not None
    assert result.perturbation_norm is not None
    assert result.evidence is not None
    assert result.evidence.decision != Decision.ALLOW


def test_stress_search_skips_already_failing_nominal_case():
    scenario = read_scenario(REVIEW_CASE)
    rules = read_rule_file(ITEMS)

    result = find_worst_case_stress(scenario, rules)

    assert result.found is False
    assert result.description is not None
    assert "already requires review" in result.description


def test_robustness_report_contains_nominal_and_uncertainty_results():
    scenario = read_scenario(REVIEW_CASE)
    rules = read_rule_file(ITEMS)

    report = build_robustness_report(scenario, rules, sample_override=15)

    assert report.scenario_id == "example-corridor-speed-review"
    assert report.nominal_decision == Decision.REQUIRE_REVIEW
    assert report.uncertainty.samples == 15
    assert report.monte_carlo.sample_count == 15
    assert report.monte_carlo.pass_count + report.monte_carlo.fail_count == 15
    assert report.monte_carlo.failure_probability >= 0.0
    assert report.repair_comparison is None


def test_robustness_report_uses_buffered_repair_for_risk_reduction():
    scenario = read_scenario(REVIEW_CASE)
    rules = read_rule_file(ITEMS)

    report = build_robustness_report(scenario, rules, sample_override=40, compare_repair=True)

    assert report.repair_comparison is not None
    assert report.repair_comparison.repair_available is True
    assert report.repair_comparison.original_failure_probability == 1.0
    assert report.repair_comparison.repaired_failure_probability is not None
    assert report.repair_comparison.repaired_failure_probability <= 0.25
    assert report.repair_comparison.absolute_risk_reduction is not None
    assert report.repair_comparison.absolute_risk_reduction >= 0.75
    assert "PATH-SPEED-001" in report.repair_comparison.fixed_rules
