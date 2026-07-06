from pathlib import Path

from src.oracle_omega.experiment import run_experiment
from src.oracle_omega.experiment_index import (
    build_benchmark_summary,
    build_experiment_index,
    write_index_outputs,
)

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "oracle" / "rules" / "starter_rules.yaml"
FRAGILE_CASE = ROOT / "oracle" / "scenarios" / "close_approach" / "fragile_corridor_pass.yaml"
REVIEW_CASE = ROOT / "oracle" / "scenarios" / "example_corridor_speed_review.yaml"


def test_experiment_index_collects_manifest_and_robustness_metrics(tmp_path: Path):
    run_experiment(
        FRAGILE_CASE,
        RULES,
        output_root=tmp_path,
        experiment_id="fragile-index-run",
        robustness=True,
        robustness_samples=20,
        tags=["fragile"],
    )
    run_experiment(
        REVIEW_CASE,
        RULES,
        output_root=tmp_path,
        experiment_id="repair-index-run",
        robustness=True,
        robustness_samples=20,
        compare_repair=True,
        tags=["repair"],
    )

    index = build_experiment_index(tmp_path)

    assert index.experiment_count == 2
    assert index.robustness_count == 2
    assert index.repair_comparison_count == 1
    assert index.decision_counts == {"ALLOW": 1, "REQUIRE_REVIEW": 1}
    assert index.family_counts == {"close_approach": 2}

    by_id = {entry.experiment_id: entry for entry in index.entries}
    fragile = by_id["fragile-index-run"]
    repair = by_id["repair-index-run"]

    assert fragile.original_failure_probability is not None
    assert fragile.original_failure_probability > 0.0
    assert fragile.repaired_failure_probability is None
    assert fragile.most_common_failure == "PATH-CORRIDOR-001"
    assert fragile.tags == ["fragile"]

    assert repair.original_failure_probability == 1.0
    assert repair.repaired_failure_probability == 0.0
    assert repair.absolute_risk_reduction == 1.0
    assert repair.tags == ["repair"]


def test_experiment_index_writes_json_and_markdown_summary(tmp_path: Path):
    run_experiment(
        REVIEW_CASE,
        RULES,
        output_root=tmp_path,
        experiment_id="repair-summary-run",
        robustness=True,
        robustness_samples=20,
        compare_repair=True,
    )
    index = build_experiment_index(tmp_path)
    index_path = tmp_path / "index.json"
    summary_path = tmp_path / "benchmark-summary.md"

    write_index_outputs(index, index_path, summary_path)

    assert index_path.exists()
    assert summary_path.exists()
    summary = summary_path.read_text(encoding="utf-8")
    assert "ORACLE-Omega Experiment Index" in summary
    assert "repair-summary-run" in summary
    assert "Risk reduction" in summary
    assert "1.000" in summary


def test_experiment_index_handles_empty_root(tmp_path: Path):
    index = build_experiment_index(tmp_path)

    assert index.experiment_count == 0
    assert index.entries == []
    assert build_benchmark_summary(index).startswith("# ORACLE-Omega Experiment Index")
