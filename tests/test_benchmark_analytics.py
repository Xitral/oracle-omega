from src.oracle_omega.benchmark_analytics import build_benchmark_analytics, render_analytics_markdown
from src.oracle_omega.experiment_index import ExperimentIndex, ExperimentIndexEntry


def make_entry(
    experiment_id: str,
    scenario_id: str,
    decision: str,
    family: str,
    original: float | None,
    repaired: float | None,
    reduction: float | None,
    rule: str | None,
    tags: list[str],
    repair: bool = False,
) -> ExperimentIndexEntry:
    return ExperimentIndexEntry(
        experiment_id=experiment_id,
        created_at_utc="2026-01-01T00:00:00Z",
        scenario_id=scenario_id,
        scenario_family=family,
        decision=decision,
        failed_count=0 if decision == "ALLOW" else 1,
        highest_severity="nominal" if decision == "ALLOW" else "critical",
        primary_rule_id=rule,
        robustness_enabled=True,
        repair_comparison_enabled=repair,
        original_failure_probability=original,
        repaired_failure_probability=repaired,
        absolute_risk_reduction=reduction,
        relative_risk_reduction=reduction,
        most_common_failure=rule,
        scenario_sha256="scenario-hash",
        rule_catalog_sha256="rules-hash",
        manifest_path=f"{experiment_id}/manifest.json",
        summary_path=f"{experiment_id}/summary.md",
        robustness_bundle_path=f"{experiment_id}/robustness_bundle.json",
        tags=tags,
    )


def test_benchmark_analytics_computes_aggregate_metrics():
    index = ExperimentIndex(
        generated_at_utc="2026-01-01T00:00:00Z",
        experiment_root="data/experiments",
        experiment_count=4,
        robustness_count=4,
        repair_comparison_count=2,
        decision_counts={"ALLOW": 2, "REQUIRE_REVIEW": 2},
        family_counts={"close_approach": 2, "surface_landing": 2},
        entries=[
            make_entry("benchmark-robust", "robust", "ALLOW", "close_approach", 0.0, None, None, None, ["benchmark"]),
            make_entry("benchmark-fragile", "fragile", "ALLOW", "close_approach", 0.5, None, None, "PATH-CORRIDOR-001", ["benchmark"]),
            make_entry("benchmark-fixed", "fixed", "REQUIRE_REVIEW", "surface_landing", 1.0, 0.0, 1.0, "PATH-SPEED-001", ["benchmark"], repair=True),
            make_entry("benchmark-residual", "residual", "REQUIRE_REVIEW", "surface_landing", 1.0, 0.2, 0.8, "LANDING-TILT-001", ["benchmark"], repair=True),
        ],
    )

    report = build_benchmark_analytics(index, repair_success_threshold=0.05)

    assert report.aggregate.experiment_count == 4
    assert report.aggregate.fragile_nominal_count == 1
    assert report.aggregate.robust_nominal_count == 1
    assert report.aggregate.repair_comparison_count == 2
    assert report.aggregate.repair_success_count == 1
    assert report.aggregate.repair_success_rate == 0.5
    assert report.aggregate.mean_repaired_failure_probability == 0.1
    assert report.aggregate.mean_absolute_risk_reduction == 0.9
    assert report.failure_mode_counts == {
        "LANDING-TILT-001": 1,
        "PATH-CORRIDOR-001": 1,
        "PATH-SPEED-001": 1,
    }


def test_benchmark_analytics_markdown_contains_paper_ready_sections():
    index = ExperimentIndex(
        generated_at_utc="2026-01-01T00:00:00Z",
        experiment_root="data/experiments",
        experiment_count=1,
        robustness_count=1,
        repair_comparison_count=1,
        decision_counts={"REQUIRE_REVIEW": 1},
        family_counts={"surface_landing": 1},
        entries=[
            make_entry("benchmark-fixed", "fixed", "REQUIRE_REVIEW", "surface_landing", 1.0, 0.0, 1.0, "PATH-SPEED-001", ["benchmark"], repair=True),
        ],
    )

    markdown = render_analytics_markdown(build_benchmark_analytics(index))

    assert "ORACLE-Omega Benchmark Analytics" in markdown
    assert "Aggregate metrics" in markdown
    assert "Risk reduction by scenario family" in markdown
    assert "Top risk-reduction cases" in markdown
    assert "Mean absolute risk reduction" in markdown
