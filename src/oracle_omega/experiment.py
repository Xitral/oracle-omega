from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from src.oracle_omega.replay import build_replay_bundle
from src.oracle_omega.robustness_bundle import build_robustness_visualization_bundle
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario
from src.oracle_omega.reviewer import review

ENGINE_VERSION = "0.1.0"
EXPERIMENT_SCHEMA_VERSION = "0.1.0"


class ExperimentArtifactPaths(BaseModel):
    manifest: str
    summary: str
    evidence: str
    replay: str
    robustness_bundle: str | None = None


class ExperimentManifest(BaseModel):
    experiment_id: str
    schema_version: str = EXPERIMENT_SCHEMA_VERSION
    engine_version: str = ENGINE_VERSION
    created_at_utc: str
    scenario_path: str
    scenario_sha256: str
    rule_catalog_path: str
    rule_catalog_sha256: str
    scenario_id: str
    scenario_family: str
    decision: str
    failed_count: int
    highest_severity: str
    primary_rule_id: str | None = None
    primary_violation_time: float | None = None
    robustness_enabled: bool = False
    robustness_samples: int | None = None
    repair_comparison_enabled: bool = False
    artifacts: ExperimentArtifactPaths
    tags: list[str] = Field(default_factory=list)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slugify(value: str) -> str:
    result = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return result or "experiment"


def short_hash(*values: str) -> str:
    payload = "|".join(values).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:10]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, BaseModel):
        data = payload.model_dump(mode="json")
    else:
        data = payload
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def relative_artifact(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def build_summary(manifest: ExperimentManifest) -> str:
    lines = [
        f"# ORACLE-Omega Experiment: `{manifest.experiment_id}`",
        "",
        "## Provenance",
        "",
        f"- Created UTC: `{manifest.created_at_utc}`",
        f"- Engine version: `{manifest.engine_version}`",
        f"- Scenario path: `{manifest.scenario_path}`",
        f"- Scenario SHA-256: `{manifest.scenario_sha256}`",
        f"- Rule catalog path: `{manifest.rule_catalog_path}`",
        f"- Rule catalog SHA-256: `{manifest.rule_catalog_sha256}`",
        "",
        "## Nominal review",
        "",
        f"- Scenario ID: `{manifest.scenario_id}`",
        f"- Scenario family: `{manifest.scenario_family}`",
        f"- Decision: `{manifest.decision}`",
        f"- Failed checks: `{manifest.failed_count}`",
        f"- Highest severity: `{manifest.highest_severity}`",
        f"- Primary rule: `{manifest.primary_rule_id}`",
        f"- Primary violation time: `{manifest.primary_violation_time}`",
        "",
    ]

    if manifest.robustness_enabled:
        lines.extend(
            [
                "## Robustness",
                "",
                f"- Robustness samples: `{manifest.robustness_samples}`",
                f"- Repair comparison enabled: `{manifest.repair_comparison_enabled}`",
                f"- Bundle: `{manifest.artifacts.robustness_bundle}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Artifacts",
            "",
            f"- Manifest: `{manifest.artifacts.manifest}`",
            f"- Evidence: `{manifest.artifacts.evidence}`",
            f"- Replay: `{manifest.artifacts.replay}`",
            f"- Summary: `{manifest.artifacts.summary}`",
            "",
            "## Reproducibility note",
            "",
            "This experiment records the exact scenario and rule-catalog hashes used for the run. Re-run the same inputs with the same engine version to reproduce the nominal review and generated replay artifacts.",
            "",
        ]
    )
    return "\n".join(lines)


def run_experiment(
    scenario_path: str | Path,
    rule_catalog_path: str | Path = Path("oracle/rules/starter_rules.yaml"),
    output_root: str | Path = Path("data/experiments"),
    robustness: bool = False,
    robustness_samples: int | None = None,
    compare_repair: bool = False,
    experiment_id: str | None = None,
    tags: list[str] | None = None,
) -> ExperimentManifest:
    scenario_file = Path(scenario_path)
    rules_file = Path(rule_catalog_path)
    root = Path(output_root)
    scenario_hash = file_sha256(scenario_file)
    rules_hash = file_sha256(rules_file)

    scenario = read_scenario(scenario_file)
    rules = read_rule_file(rules_file)
    evidence = review(scenario, rules)
    replay = build_replay_bundle(scenario, evidence)

    created = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    run_id = experiment_id or f"{slugify(scenario.id)}-{short_hash(scenario_hash, rules_hash, created)}"
    experiment_dir = root / run_id

    manifest_path = experiment_dir / "manifest.json"
    summary_path = experiment_dir / "summary.md"
    evidence_path = experiment_dir / "evidence.json"
    replay_path = experiment_dir / "replay.json"
    bundle_path = experiment_dir / "robustness_bundle.json" if robustness else None

    robustness_bundle = None
    if robustness:
        robustness_bundle = build_robustness_visualization_bundle(
            scenario,
            rules,
            sample_override=robustness_samples,
            compare_repair=compare_repair,
        )

    artifacts = ExperimentArtifactPaths(
        manifest=relative_artifact(manifest_path, experiment_dir),
        summary=relative_artifact(summary_path, experiment_dir),
        evidence=relative_artifact(evidence_path, experiment_dir),
        replay=relative_artifact(replay_path, experiment_dir),
        robustness_bundle=relative_artifact(bundle_path, experiment_dir) if bundle_path else None,
    )

    manifest = ExperimentManifest(
        experiment_id=run_id,
        created_at_utc=created,
        scenario_path=str(scenario_file).replace("\\", "/"),
        scenario_sha256=scenario_hash,
        rule_catalog_path=str(rules_file).replace("\\", "/"),
        rule_catalog_sha256=rules_hash,
        scenario_id=scenario.id,
        scenario_family=scenario.family,
        decision=str(evidence.decision.value),
        failed_count=evidence.failed_count,
        highest_severity=evidence.highest_severity,
        primary_rule_id=evidence.primary_rule_id,
        primary_violation_time=evidence.primary_violation_time,
        robustness_enabled=robustness,
        robustness_samples=robustness_samples,
        repair_comparison_enabled=compare_repair,
        artifacts=artifacts,
        tags=tags or [],
    )

    write_json(evidence_path, evidence)
    write_json(replay_path, replay)
    if bundle_path is not None and robustness_bundle is not None:
        write_json(bundle_path, robustness_bundle)
    write_text(summary_path, build_summary(manifest))
    write_json(manifest_path, manifest)
    return manifest
