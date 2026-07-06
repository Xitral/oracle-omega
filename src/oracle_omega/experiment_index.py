from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ExperimentIndexEntry(BaseModel):
    experiment_id: str
    created_at_utc: str
    scenario_id: str
    scenario_family: str
    decision: str
    failed_count: int
    highest_severity: str
    primary_rule_id: str | None = None
    robustness_enabled: bool = False
    repair_comparison_enabled: bool = False
    original_failure_probability: float | None = None
    repaired_failure_probability: float | None = None
    absolute_risk_reduction: float | None = None
    relative_risk_reduction: float | None = None
    most_common_failure: str | None = None
    scenario_sha256: str
    rule_catalog_sha256: str
    manifest_path: str
    summary_path: str
    robustness_bundle_path: str | None = None
    tags: list[str] = Field(default_factory=list)


class ExperimentIndex(BaseModel):
    generated_at_utc: str
    experiment_root: str
    experiment_count: int
    robustness_count: int
    repair_comparison_count: int
    decision_counts: dict[str, int] = Field(default_factory=dict)
    family_counts: dict[str, int] = Field(default_factory=dict)
    entries: list[ExperimentIndexEntry] = Field(default_factory=list)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def as_repo_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def find_manifest_paths(experiment_root: Path) -> list[Path]:
    if not experiment_root.exists():
        return []
    return sorted(
        path for path in experiment_root.glob("*/manifest.json")
        if path.parent.name not in {".", ".."}
    )


def robustness_metrics(bundle_path: Path | None) -> dict:
    if bundle_path is None or not bundle_path.exists():
        return {}
    bundle = read_json(bundle_path)
    report = bundle.get("robustness_report", {})
    monte_carlo = report.get("monte_carlo", {})
    comparison = report.get("repair_comparison") or {}
    return {
        "original_failure_probability": monte_carlo.get("failure_probability"),
        "repaired_failure_probability": comparison.get("repaired_failure_probability"),
        "absolute_risk_reduction": comparison.get("absolute_risk_reduction"),
        "relative_risk_reduction": comparison.get("relative_risk_reduction"),
        "most_common_failure": monte_carlo.get("most_common_failure"),
    }


def build_entry(manifest_path: Path, experiment_root: Path) -> ExperimentIndexEntry:
    manifest = read_json(manifest_path)
    run_dir = manifest_path.parent
    artifacts = manifest.get("artifacts", {})
    summary_file = run_dir / artifacts.get("summary", "summary.md")
    bundle_rel = artifacts.get("robustness_bundle")
    bundle_file = run_dir / bundle_rel if bundle_rel else None
    metrics = robustness_metrics(bundle_file)

    return ExperimentIndexEntry(
        experiment_id=manifest["experiment_id"],
        created_at_utc=manifest["created_at_utc"],
        scenario_id=manifest["scenario_id"],
        scenario_family=manifest["scenario_family"],
        decision=manifest["decision"],
        failed_count=int(manifest["failed_count"]),
        highest_severity=manifest["highest_severity"],
        primary_rule_id=manifest.get("primary_rule_id"),
        robustness_enabled=bool(manifest.get("robustness_enabled", False)),
        repair_comparison_enabled=bool(manifest.get("repair_comparison_enabled", False)),
        original_failure_probability=metrics.get("original_failure_probability"),
        repaired_failure_probability=metrics.get("repaired_failure_probability"),
        absolute_risk_reduction=metrics.get("absolute_risk_reduction"),
        relative_risk_reduction=metrics.get("relative_risk_reduction"),
        most_common_failure=metrics.get("most_common_failure"),
        scenario_sha256=manifest["scenario_sha256"],
        rule_catalog_sha256=manifest["rule_catalog_sha256"],
        manifest_path=as_repo_path(manifest_path, experiment_root),
        summary_path=as_repo_path(summary_file, experiment_root),
        robustness_bundle_path=as_repo_path(bundle_file, experiment_root) if bundle_file else None,
        tags=manifest.get("tags", []),
    )


def build_experiment_index(experiment_root: str | Path = Path("data/experiments")) -> ExperimentIndex:
    root = Path(experiment_root)
    entries = [build_entry(path, root) for path in find_manifest_paths(root)]
    decision_counts = Counter(entry.decision for entry in entries)
    family_counts = Counter(entry.scenario_family for entry in entries)
    return ExperimentIndex(
        generated_at_utc=utc_timestamp(),
        experiment_root=str(root).replace("\\", "/"),
        experiment_count=len(entries),
        robustness_count=sum(1 for entry in entries if entry.robustness_enabled),
        repair_comparison_count=sum(1 for entry in entries if entry.repair_comparison_enabled),
        decision_counts=dict(sorted(decision_counts.items())),
        family_counts=dict(sorted(family_counts.items())),
        entries=entries,
    )


def risk_text(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def build_benchmark_summary(index: ExperimentIndex) -> str:
    lines = [
        "# ORACLE-Omega Experiment Index",
        "",
        "## Overview",
        "",
        f"- Generated UTC: `{index.generated_at_utc}`",
        f"- Experiment root: `{index.experiment_root}`",
        f"- Experiments indexed: `{index.experiment_count}`",
        f"- Robustness experiments: `{index.robustness_count}`",
        f"- Repair comparison experiments: `{index.repair_comparison_count}`",
        f"- Decisions: `{index.decision_counts}`",
        f"- Scenario families: `{index.family_counts}`",
        "",
        "## Experiments",
        "",
        "| Experiment | Scenario | Decision | Failed | Original risk | Repaired risk | Risk reduction | Common failure |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for entry in index.entries:
        lines.append(
            "| "
            f"`{entry.experiment_id}` | "
            f"`{entry.scenario_id}` | "
            f"`{entry.decision}` | "
            f"{entry.failed_count} | "
            f"{risk_text(entry.original_failure_probability)} | "
            f"{risk_text(entry.repaired_failure_probability)} | "
            f"{risk_text(entry.absolute_risk_reduction)} | "
            f"`{entry.most_common_failure}` |"
        )

    lines.extend(
        [
            "",
            "## Reproducibility",
            "",
            "Each row points back to an experiment manifest that records the scenario hash and rule-catalog hash used for that run.",
            "",
        ]
    )
    return "\n".join(lines)


def write_index_outputs(
    index: ExperimentIndex,
    index_path: str | Path,
    summary_path: str | Path,
) -> None:
    index_file = Path(index_path)
    summary_file = Path(summary_path)
    index_file.parent.mkdir(parents=True, exist_ok=True)
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    index_file.write_text(json.dumps(index.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    summary_file.write_text(build_benchmark_summary(index), encoding="utf-8")
