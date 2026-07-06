from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from src.oracle_omega.benchmark_analytics import BenchmarkAnalyticsReport


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def metric_text(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


class BenchmarkClaim(BaseModel):
    claim_id: str
    title: str
    statement: str
    scope: str
    evidence: dict[str, int | float | str | None] = Field(default_factory=dict)
    caveat: str


class BenchmarkClaimsReport(BaseModel):
    generated_at_utc: str
    source_generated_at_utc: str
    claim_count: int
    claims: list[BenchmarkClaim] = Field(default_factory=list)


def load_analytics_report(path: str | Path) -> BenchmarkAnalyticsReport:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return BenchmarkAnalyticsReport.model_validate(data)


def build_benchmark_claims(report: BenchmarkAnalyticsReport) -> BenchmarkClaimsReport:
    aggregate = report.aggregate
    claims: list[BenchmarkClaim] = []

    claims.append(
        BenchmarkClaim(
            claim_id="repair-success-rate",
            title="Buffered repair success rate",
            statement=(
                "Buffered repair met the configured repaired-risk threshold in "
                f"{aggregate.repair_success_count} of {aggregate.repair_comparison_count} benchmark repair comparisons."
            ),
            scope="Benchmark-tagged experiments only.",
            evidence={
                "repair_success_count": aggregate.repair_success_count,
                "repair_comparison_count": aggregate.repair_comparison_count,
                "repair_success_rate": aggregate.repair_success_rate,
                "repair_success_threshold": report.repair_success_threshold,
            },
            caveat="Threshold results are scoped to this benchmark run.",
        )
    )

    claims.append(
        BenchmarkClaim(
            claim_id="mean-risk-reduction",
            title="Mean robustness risk reduction",
            statement=(
                "Across benchmark repair comparisons, mean failure probability decreased from "
                f"{metric_text(aggregate.mean_repair_original_failure_probability)} to "
                f"{metric_text(aggregate.mean_repaired_failure_probability)}, with mean absolute risk reduction "
                f"{metric_text(aggregate.mean_absolute_risk_reduction)}."
            ),
            scope="Benchmark-tagged repair comparisons with robustness measurements.",
            evidence={
                "mean_repair_original_failure_probability": aggregate.mean_repair_original_failure_probability,
                "median_repair_original_failure_probability": aggregate.median_repair_original_failure_probability,
                "mean_repaired_failure_probability": aggregate.mean_repaired_failure_probability,
                "mean_absolute_risk_reduction": aggregate.mean_absolute_risk_reduction,
                "median_absolute_risk_reduction": aggregate.median_absolute_risk_reduction,
            },
            caveat="Metrics depend on the current scenario corpus, uncertainty assumptions, and sample count.",
        )
    )

    if aggregate.fragile_nominal_count > 0:
        claims.append(
            BenchmarkClaim(
                claim_id="fragile-nominal-detection",
                title="Fragile nominal scenario detection",
                statement=(
                    "ORACLE-Omega identified nominally allowed benchmark scenarios with nonzero uncertainty risk; "
                    f"fragile nominal count was {aggregate.fragile_nominal_count}."
                ),
                scope="Benchmark-tagged nominal scenarios with robustness evaluation.",
                evidence={
                    "fragile_nominal_count": aggregate.fragile_nominal_count,
                    "robust_nominal_count": aggregate.robust_nominal_count,
                },
                caveat="A fragile nominal case is defined by nonzero sampled uncertainty risk.",
            )
        )

    if report.failure_mode_counts:
        top_failure, top_count = max(report.failure_mode_counts.items(), key=lambda item: item[1])
        claims.append(
            BenchmarkClaim(
                claim_id="dominant-failure-mode",
                title="Dominant uncertainty failure mode",
                statement=f"The most frequent benchmark failure mode was {top_failure}, observed in {top_count} indexed cases.",
                scope="Benchmark-tagged experiments with a recorded most-common failure mode.",
                evidence={
                    "top_failure_mode": top_failure,
                    "top_failure_mode_count": top_count,
                },
                caveat="Counts summarize the recorded most-common failure mode per experiment.",
            )
        )

    return BenchmarkClaimsReport(
        generated_at_utc=utc_timestamp(),
        source_generated_at_utc=report.generated_at_utc,
        claim_count=len(claims),
        claims=claims,
    )


def render_claims_markdown(report: BenchmarkClaimsReport) -> str:
    lines = [
        "# ORACLE-Omega Benchmark Claim Cards",
        "",
        f"- Generated UTC: `{report.generated_at_utc}`",
        f"- Source analytics UTC: `{report.source_generated_at_utc}`",
        f"- Claims: `{report.claim_count}`",
        "",
    ]
    for claim in report.claims:
        lines.extend(
            [
                f"## {claim.title}",
                "",
                claim.statement,
                "",
                f"- Claim ID: `{claim.claim_id}`",
                f"- Scope: {claim.scope}",
                f"- Evidence: `{claim.evidence}`",
                f"- Caveat: {claim.caveat}",
                "",
            ]
        )
    return "\n".join(lines)


def write_claim_outputs(
    report: BenchmarkClaimsReport,
    json_path: str | Path,
    markdown_path: str | Path,
) -> None:
    json_file = Path(json_path)
    markdown_file = Path(markdown_path)
    json_file.parent.mkdir(parents=True, exist_ok=True)
    markdown_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    markdown_file.write_text(render_claims_markdown(report), encoding="utf-8")
