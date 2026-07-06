from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from src.oracle_omega.experiment_index import ExperimentIndex, ExperimentIndexEntry


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def mean_or_none(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def median_or_none(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def metric_text(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


class BenchmarkAggregateMetrics(BaseModel):
    experiment_count: int
    benchmark_experiment_count: int
    robustness_count: int
    repair_comparison_count: int
    fragile_nominal_count: int
    robust_nominal_count: int
    repaired_zero_risk_count: int
    repaired_remaining_risk_count: int
    repair_success_count: int
    repair_success_rate: float | None
    mean_original_failure_probability: float | None
    mean_repaired_failure_probability: float | None
    mean_absolute_risk_reduction: float | None
    median_absolute_risk_reduction: float | None
    mean_relative_risk_reduction: float | None
    median_relative_risk_reduction: float | None


class BenchmarkGroupMetrics(BaseModel):
    key: str
    experiment_count: int
    fragile_nominal_count: int
    repair_comparison_count: int
    repair_success_count: int
    repair_success_rate: float | None
    mean_original_failure_probability: float | None
    mean_repaired_failure_probability: float | None
    mean_absolute_risk_reduction: float | None
    median_absolute_risk_reduction: float | None


class BenchmarkCaseHighlight(BaseModel):
    experiment_id: str
    scenario_id: str
    scenario_family: str
    decision: str
    primary_rule_id: str | None = None
    most_common_failure: str | None = None
    original_failure_probability: float | None = None
    repaired_failure_probability: float | None = None
    absolute_risk_reduction: float | None = None


class BenchmarkAnalyticsReport(BaseModel):
    generated_at_utc: str
    source_experiment_count: int
    repair_success_threshold: float
    aggregate: BenchmarkAggregateMetrics
    failure_mode_counts: dict[str, int] = Field(default_factory=dict)
    metrics_by_family: list[BenchmarkGroupMetrics] = Field(default_factory=list)
    metrics_by_rule: list[BenchmarkGroupMetrics] = Field(default_factory=list)
    fragile_nominal_cases: list[BenchmarkCaseHighlight] = Field(default_factory=list)
    remaining_risk_cases: list[BenchmarkCaseHighlight] = Field(default_factory=list)
    top_risk_reduction_cases: list[BenchmarkCaseHighlight] = Field(default_factory=list)


def load_experiment_index(path: str | Path) -> ExperimentIndex:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ExperimentIndex.model_validate(data)


def is_benchmark_entry(entry: ExperimentIndexEntry) -> bool:
    return "benchmark" in entry.tags or entry.experiment_id.startswith("benchmark-")


def has_risk(value: float | None) -> bool:
    return value is not None and value > 0.0


def repair_entries(entries: list[ExperimentIndexEntry]) -> list[ExperimentIndexEntry]:
    return [entry for entry in entries if entry.repair_comparison_enabled]


def successful_repair(entry: ExperimentIndexEntry, threshold: float) -> bool:
    return entry.repaired_failure_probability is not None and entry.repaired_failure_probability <= threshold


def highlight(entry: ExperimentIndexEntry) -> BenchmarkCaseHighlight:
    return BenchmarkCaseHighlight(
        experiment_id=entry.experiment_id,
        scenario_id=entry.scenario_id,
        scenario_family=entry.scenario_family,
        decision=entry.decision,
        primary_rule_id=entry.primary_rule_id,
        most_common_failure=entry.most_common_failure,
        original_failure_probability=entry.original_failure_probability,
        repaired_failure_probability=entry.repaired_failure_probability,
        absolute_risk_reduction=entry.absolute_risk_reduction,
    )


def group_metrics(
    key: str,
    entries: list[ExperimentIndexEntry],
    repair_success_threshold: float,
) -> BenchmarkGroupMetrics:
    repairs = repair_entries(entries)
    successes = [entry for entry in repairs if successful_repair(entry, repair_success_threshold)]
    original_risks = [entry.original_failure_probability for entry in entries if entry.original_failure_probability is not None]
    repaired_risks = [entry.repaired_failure_probability for entry in repairs if entry.repaired_failure_probability is not None]
    absolute_reductions = [entry.absolute_risk_reduction for entry in repairs if entry.absolute_risk_reduction is not None]
    return BenchmarkGroupMetrics(
        key=key,
        experiment_count=len(entries),
        fragile_nominal_count=sum(
            1 for entry in entries if entry.decision == "ALLOW" and has_risk(entry.original_failure_probability)
        ),
        repair_comparison_count=len(repairs),
        repair_success_count=len(successes),
        repair_success_rate=rate(len(successes), len(repairs)),
        mean_original_failure_probability=mean_or_none(original_risks),
        mean_repaired_failure_probability=mean_or_none(repaired_risks),
        mean_absolute_risk_reduction=mean_or_none(absolute_reductions),
        median_absolute_risk_reduction=median_or_none(absolute_reductions),
    )


def grouped(entries: list[ExperimentIndexEntry], key_fn) -> dict[str, list[ExperimentIndexEntry]]:
    buckets: dict[str, list[ExperimentIndexEntry]] = defaultdict(list)
    for entry in entries:
        key = key_fn(entry)
        if key:
            buckets[key].append(entry)
    return dict(sorted(buckets.items()))


def build_benchmark_analytics(
    index: ExperimentIndex,
    repair_success_threshold: float = 0.05,
    benchmark_only: bool = True,
) -> BenchmarkAnalyticsReport:
    source_entries = list(index.entries)
    entries = [entry for entry in source_entries if is_benchmark_entry(entry)] if benchmark_only else source_entries
    repairs = repair_entries(entries)
    successful_repairs = [entry for entry in repairs if successful_repair(entry, repair_success_threshold)]
    original_risks = [entry.original_failure_probability for entry in entries if entry.original_failure_probability is not None]
    repaired_risks = [entry.repaired_failure_probability for entry in repairs if entry.repaired_failure_probability is not None]
    absolute_reductions = [entry.absolute_risk_reduction for entry in repairs if entry.absolute_risk_reduction is not None]
    relative_reductions = [entry.relative_risk_reduction for entry in repairs if entry.relative_risk_reduction is not None]

    fragile_nominal_cases = [
        entry for entry in entries if entry.decision == "ALLOW" and has_risk(entry.original_failure_probability)
    ]
    robust_nominal_cases = [
        entry for entry in entries if entry.decision == "ALLOW" and entry.original_failure_probability == 0.0
    ]
    zero_risk_repairs = [entry for entry in repairs if entry.repaired_failure_probability == 0.0]
    remaining_risk_repairs = [
        entry for entry in repairs if entry.repaired_failure_probability is not None and entry.repaired_failure_probability > 0.0
    ]

    failure_mode_counts = Counter(
        entry.most_common_failure for entry in entries if entry.most_common_failure is not None
    )

    by_family = [
        group_metrics(key, values, repair_success_threshold)
        for key, values in grouped(entries, lambda entry: entry.scenario_family).items()
    ]
    by_rule = [
        group_metrics(key, values, repair_success_threshold)
        for key, values in grouped(entries, lambda entry: entry.primary_rule_id or entry.most_common_failure).items()
    ]

    return BenchmarkAnalyticsReport(
        generated_at_utc=utc_timestamp(),
        source_experiment_count=len(source_entries),
        repair_success_threshold=repair_success_threshold,
        aggregate=BenchmarkAggregateMetrics(
            experiment_count=len(entries),
            benchmark_experiment_count=sum(1 for entry in entries if is_benchmark_entry(entry)),
            robustness_count=sum(1 for entry in entries if entry.robustness_enabled),
            repair_comparison_count=len(repairs),
            fragile_nominal_count=len(fragile_nominal_cases),
            robust_nominal_count=len(robust_nominal_cases),
            repaired_zero_risk_count=len(zero_risk_repairs),
            repaired_remaining_risk_count=len(remaining_risk_repairs),
            repair_success_count=len(successful_repairs),
            repair_success_rate=rate(len(successful_repairs), len(repairs)),
            mean_original_failure_probability=mean_or_none(original_risks),
            mean_repaired_failure_probability=mean_or_none(repaired_risks),
            mean_absolute_risk_reduction=mean_or_none(absolute_reductions),
            median_absolute_risk_reduction=median_or_none(absolute_reductions),
            mean_relative_risk_reduction=mean_or_none(relative_reductions),
            median_relative_risk_reduction=median_or_none(relative_reductions),
        ),
        failure_mode_counts=dict(sorted(failure_mode_counts.items())),
        metrics_by_family=by_family,
        metrics_by_rule=by_rule,
        fragile_nominal_cases=[highlight(entry) for entry in fragile_nominal_cases],
        remaining_risk_cases=[highlight(entry) for entry in remaining_risk_repairs],
        top_risk_reduction_cases=[
            highlight(entry)
            for entry in sorted(
                repairs,
                key=lambda entry: entry.absolute_risk_reduction if entry.absolute_risk_reduction is not None else -1.0,
                reverse=True,
            )[:5]
        ],
    )


def render_analytics_markdown(report: BenchmarkAnalyticsReport) -> str:
    aggregate = report.aggregate
    lines = [
        "# ORACLE-Omega Benchmark Analytics",
        "",
        "## Aggregate metrics",
        "",
        f"- Generated UTC: `{report.generated_at_utc}`",
        f"- Experiments analyzed: `{aggregate.experiment_count}`",
        f"- Robustness experiments: `{aggregate.robustness_count}`",
        f"- Repair comparisons: `{aggregate.repair_comparison_count}`",
        f"- Repair success threshold: `{report.repair_success_threshold}`",
        f"- Repair success rate: `{metric_text(aggregate.repair_success_rate)}`",
        f"- Mean original failure probability: `{metric_text(aggregate.mean_original_failure_probability)}`",
        f"- Mean repaired failure probability: `{metric_text(aggregate.mean_repaired_failure_probability)}`",
        f"- Mean absolute risk reduction: `{metric_text(aggregate.mean_absolute_risk_reduction)}`",
        f"- Median absolute risk reduction: `{metric_text(aggregate.median_absolute_risk_reduction)}`",
        f"- Fragile nominal cases: `{aggregate.fragile_nominal_count}`",
        f"- Robust nominal cases: `{aggregate.robust_nominal_count}`",
        f"- Zero-risk repaired cases: `{aggregate.repaired_zero_risk_count}`",
        f"- Remaining-risk repaired cases: `{aggregate.repaired_remaining_risk_count}`",
        "",
        "## Risk reduction by scenario family",
        "",
        "| Family | Experiments | Repairs | Success rate | Mean original risk | Mean repaired risk | Mean risk reduction |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in report.metrics_by_family:
        lines.append(
            f"| `{item.key}` | {item.experiment_count} | {item.repair_comparison_count} | "
            f"{metric_text(item.repair_success_rate)} | {metric_text(item.mean_original_failure_probability)} | "
            f"{metric_text(item.mean_repaired_failure_probability)} | {metric_text(item.mean_absolute_risk_reduction)} |"
        )

    lines.extend(
        [
            "",
            "## Risk reduction by rule/failure mode",
            "",
            "| Rule / failure mode | Experiments | Repairs | Success rate | Mean repaired risk | Mean risk reduction |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in report.metrics_by_rule:
        lines.append(
            f"| `{item.key}` | {item.experiment_count} | {item.repair_comparison_count} | "
            f"{metric_text(item.repair_success_rate)} | {metric_text(item.mean_repaired_failure_probability)} | "
            f"{metric_text(item.mean_absolute_risk_reduction)} |"
        )

    lines.extend(
        [
            "",
            "## Fragile nominal cases",
            "",
            "| Scenario | Original risk | Common failure |",
            "| --- | ---: | --- |",
        ]
    )
    for item in report.fragile_nominal_cases:
        lines.append(
            f"| `{item.scenario_id}` | {metric_text(item.original_failure_probability)} | `{item.most_common_failure}` |"
        )

    lines.extend(
        [
            "",
            "## Remaining-risk repaired cases",
            "",
            "| Scenario | Rule | Original risk | Repaired risk | Risk reduction |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for item in report.remaining_risk_cases:
        lines.append(
            f"| `{item.scenario_id}` | `{item.primary_rule_id or item.most_common_failure}` | "
            f"{metric_text(item.original_failure_probability)} | {metric_text(item.repaired_failure_probability)} | "
            f"{metric_text(item.absolute_risk_reduction)} |"
        )

    lines.extend(
        [
            "",
            "## Top risk-reduction cases",
            "",
            "| Scenario | Original risk | Repaired risk | Risk reduction |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in report.top_risk_reduction_cases:
        lines.append(
            f"| `{item.scenario_id}` | {metric_text(item.original_failure_probability)} | "
            f"{metric_text(item.repaired_failure_probability)} | {metric_text(item.absolute_risk_reduction)} |"
        )

    lines.append("")
    return "\n".join(lines)


def write_analytics_outputs(
    report: BenchmarkAnalyticsReport,
    json_path: str | Path,
    markdown_path: str | Path,
) -> None:
    json_file = Path(json_path)
    markdown_file = Path(markdown_path)
    json_file.parent.mkdir(parents=True, exist_ok=True)
    markdown_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    markdown_file.write_text(render_analytics_markdown(report), encoding="utf-8")
