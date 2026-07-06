from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from src.oracle_omega.benchmark_analytics import (
    BenchmarkAnalyticsReport,
    build_benchmark_analytics,
    write_analytics_outputs,
)
from src.oracle_omega.benchmark_claims import BenchmarkClaimsReport, build_benchmark_claims, write_claim_outputs
from src.oracle_omega.core.models import Decision
from src.oracle_omega.experiment import ExperimentManifest, run_experiment, slugify
from src.oracle_omega.experiment_index import ExperimentIndex, build_experiment_index, write_index_outputs
from src.oracle_omega.reviewer import review
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario
from src.oracle_omega.suite_runner import scenario_files


class BenchmarkSkippedCase(BaseModel):
    path: str
    reason: str


class BenchmarkExperimentRun(BaseModel):
    path: str
    experiment_id: str
    scenario_id: str
    scenario_family: str
    decision: str
    highest_severity: str
    failed_count: int
    repair_comparison_enabled: bool


class BenchmarkExperimentSummary(BaseModel):
    suite_root: str
    output_root: str
    generated_count: int
    skipped_count: int
    index_path: str
    summary_path: str
    analytics_path: str
    analytics_summary_path: str
    claims_path: str
    claims_summary_path: str
    generated: list[BenchmarkExperimentRun] = Field(default_factory=list)
    skipped: list[BenchmarkSkippedCase] = Field(default_factory=list)
    index: ExperimentIndex
    analytics: BenchmarkAnalyticsReport
    claims: BenchmarkClaimsReport


def run_id_for_scenario(scenario_id: str) -> str:
    return f"benchmark-{slugify(scenario_id)}"


def experiment_tags(family: str, decision: Decision, severity: str, repair: bool) -> list[str]:
    tags = ["benchmark", family, decision.value.lower(), severity]
    if repair:
        tags.append("repair-comparison")
    return tags


def should_compare_repair(decision: Decision, failed_count: int) -> bool:
    return decision != Decision.ALLOW and failed_count > 0


def run_benchmark_experiments(
    suite_root: str | Path = Path("oracle/scenarios"),
    rule_catalog_path: str | Path = Path("oracle/rules/starter_rules.yaml"),
    output_root: str | Path = Path("data/experiments"),
    samples: int = 100,
    index_path: str | Path | None = None,
    summary_path: str | Path | None = None,
    analytics_path: str | Path | None = None,
    analytics_summary_path: str | Path | None = None,
    claims_path: str | Path | None = None,
    claims_summary_path: str | Path | None = None,
    repair_success_threshold: float = 0.05,
) -> BenchmarkExperimentSummary:
    suite = Path(suite_root)
    rules_path = Path(rule_catalog_path)
    out = Path(output_root)
    index_out = Path(index_path) if index_path is not None else out / "index.json"
    summary_out = Path(summary_path) if summary_path is not None else out / "benchmark-summary.md"
    analytics_out = Path(analytics_path) if analytics_path is not None else out / "benchmark-analytics.json"
    analytics_summary_out = (
        Path(analytics_summary_path) if analytics_summary_path is not None else out / "benchmark-analytics.md"
    )
    claims_out = Path(claims_path) if claims_path is not None else out / "benchmark-claims.json"
    claims_summary_out = Path(claims_summary_path) if claims_summary_path is not None else out / "benchmark-claims.md"
    rules = read_rule_file(rules_path)

    generated: list[BenchmarkExperimentRun] = []
    skipped: list[BenchmarkSkippedCase] = []

    for path in scenario_files(suite):
        try:
            scenario = read_scenario(path)
            evidence = review(scenario, rules)
        except Exception as exc:  # noqa: BLE001 - benchmark runner records invalid fixtures.
            skipped.append(BenchmarkSkippedCase(path=str(path), reason=str(exc)))
            continue

        compare_repair = should_compare_repair(evidence.decision, evidence.failed_count)
        experiment_id = run_id_for_scenario(scenario.id)
        manifest: ExperimentManifest = run_experiment(
            scenario_path=path,
            rule_catalog_path=rules_path,
            output_root=out,
            robustness=True,
            robustness_samples=samples,
            compare_repair=compare_repair,
            experiment_id=experiment_id,
            tags=experiment_tags(scenario.family, evidence.decision, evidence.highest_severity, compare_repair),
        )
        generated.append(
            BenchmarkExperimentRun(
                path=str(path),
                experiment_id=manifest.experiment_id,
                scenario_id=manifest.scenario_id,
                scenario_family=manifest.scenario_family,
                decision=manifest.decision,
                highest_severity=manifest.highest_severity,
                failed_count=manifest.failed_count,
                repair_comparison_enabled=compare_repair,
            )
        )

    index = build_experiment_index(out)
    write_index_outputs(index, index_out, summary_out)
    analytics = build_benchmark_analytics(
        index,
        repair_success_threshold=repair_success_threshold,
        benchmark_only=True,
    )
    write_analytics_outputs(analytics, analytics_out, analytics_summary_out)
    claims = build_benchmark_claims(analytics)
    write_claim_outputs(claims, claims_out, claims_summary_out)

    return BenchmarkExperimentSummary(
        suite_root=str(suite).replace("\\", "/"),
        output_root=str(out).replace("\\", "/"),
        generated_count=len(generated),
        skipped_count=len(skipped),
        index_path=str(index_out).replace("\\", "/"),
        summary_path=str(summary_out).replace("\\", "/"),
        analytics_path=str(analytics_out).replace("\\", "/"),
        analytics_summary_path=str(analytics_summary_out).replace("\\", "/"),
        claims_path=str(claims_out).replace("\\", "/"),
        claims_summary_path=str(claims_summary_out).replace("\\", "/"),
        generated=generated,
        skipped=skipped,
        index=index,
        analytics=analytics,
        claims=claims,
    )
