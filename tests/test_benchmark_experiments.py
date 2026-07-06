from pathlib import Path

from src.oracle_omega.benchmark_experiments import run_benchmark_experiments

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "oracle" / "rules" / "starter_rules.yaml"
SCENARIOS = ROOT / "oracle" / "scenarios"


def test_benchmark_experiment_runner_generates_valid_suite_experiments(tmp_path: Path):
    summary = run_benchmark_experiments(
        suite_root=SCENARIOS,
        rule_catalog_path=RULES,
        output_root=tmp_path,
        samples=10,
    )

    assert summary.generated_count >= 12
    assert summary.skipped_count >= 3
    assert summary.index.experiment_count == summary.generated_count
    assert summary.index.robustness_count == summary.generated_count
    assert summary.index.repair_comparison_count >= 1
    assert (tmp_path / "index.json").exists()
    assert (tmp_path / "benchmark-summary.md").exists()

    generated_by_id = {item.scenario_id: item for item in summary.generated}
    assert "example-corridor-speed-review" in generated_by_id
    assert generated_by_id["example-corridor-speed-review"].repair_comparison_enabled is True
    assert "close-approach-fragile-corridor-pass" in generated_by_id
    assert generated_by_id["close-approach-fragile-corridor-pass"].repair_comparison_enabled is False

    index_by_id = {entry.scenario_id: entry for entry in summary.index.entries}
    tilt_entry = index_by_id["surface-landing-tilt-failure"]
    assert tilt_entry.original_failure_probability == 1.0
    assert tilt_entry.repaired_failure_probability is not None
    assert tilt_entry.repaired_failure_probability <= 0.25
    assert tilt_entry.absolute_risk_reduction is not None
    assert tilt_entry.absolute_risk_reduction >= 0.75

    assert all("stress" in skipped.path for skipped in summary.skipped)


def test_benchmark_experiment_runner_writes_research_index_summary(tmp_path: Path):
    summary = run_benchmark_experiments(
        suite_root=SCENARIOS,
        rule_catalog_path=RULES,
        output_root=tmp_path,
        samples=10,
        index_path=tmp_path / "custom-index.json",
        summary_path=tmp_path / "custom-summary.md",
    )

    assert summary.index_path.endswith("custom-index.json")
    assert summary.summary_path.endswith("custom-summary.md")
    assert (tmp_path / "custom-index.json").exists()
    assert (tmp_path / "custom-summary.md").exists()
    markdown = (tmp_path / "custom-summary.md").read_text(encoding="utf-8")
    assert "ORACLE-Omega Experiment Index" in markdown
    assert "| Experiment | Scenario | Decision |" in markdown
    assert "`REQUIRE_REVIEW` |" in markdown
