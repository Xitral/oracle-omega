from pathlib import Path

from src.oracle_omega.buffered_repair import build_buffered_repair_candidate
from src.oracle_omega.robustness import build_robustness_report
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "oracle" / "rules" / "starter_rules.yaml"
TILT_CASE = ROOT / "oracle" / "scenarios" / "surface_landing" / "tilt_failure.yaml"


def test_buffered_repair_fixes_tilt_rule_deterministically():
    scenario = read_scenario(TILT_CASE)
    rules = read_rule_file(RULES)

    repair = build_buffered_repair_candidate(scenario, rules)

    assert repair.available is True
    assert "LANDING-TILT-001" in repair.fixed_rules
    assert repair.remaining_failures == []
    assert repair.repaired_evidence is not None
    assert repair.repaired_evidence.failed_count == 0


def test_buffered_repair_reduces_tilt_uncertainty_risk():
    scenario = read_scenario(TILT_CASE)
    rules = read_rule_file(RULES)

    report = build_robustness_report(scenario, rules, sample_override=40, compare_repair=True)

    assert report.repair_comparison is not None
    assert report.repair_comparison.repair_available is True
    assert report.repair_comparison.original_failure_probability == 1.0
    assert report.repair_comparison.repaired_failure_probability is not None
    assert report.repair_comparison.repaired_failure_probability <= 0.25
    assert report.repair_comparison.absolute_risk_reduction is not None
    assert report.repair_comparison.absolute_risk_reduction >= 0.75
