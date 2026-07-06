from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field

from src.oracle_omega.experiment import run_experiment
from src.oracle_omega.robustness_bundle import build_robustness_visualization_bundle
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.suite_runner import run_suite
from src.oracle_omega.scenario_file import read_scenario

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES = ROOT / "oracle" / "rules" / "starter_rules.yaml"
DEFAULT_SCENARIOS = ROOT / "oracle" / "scenarios"
FRAGILE_SCENARIO = DEFAULT_SCENARIOS / "close_approach" / "fragile_corridor_pass.yaml"
REPAIR_SCENARIO = DEFAULT_SCENARIOS / "example_corridor_speed_review.yaml"
THEATER_FILES = [ROOT / "web" / "index.html", ROOT / "web" / "robustness.html"]


class ReleaseValidationCheck(BaseModel):
    name: str
    passed: bool
    detail: str


class ReleaseValidationReport(BaseModel):
    passed: bool
    checks: list[ReleaseValidationCheck] = Field(default_factory=list)


def add_check(checks: list[ReleaseValidationCheck], name: str, condition: bool, detail: str) -> None:
    checks.append(ReleaseValidationCheck(name=name, passed=condition, detail=detail))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_suite(checks: list[ReleaseValidationCheck]) -> None:
    summary = run_suite(DEFAULT_SCENARIOS, DEFAULT_RULES)
    require(summary.total_cases >= 14, f"Expected at least 14 suite cases, got {summary.total_cases}.")
    require(summary.valid_cases >= 11, f"Expected at least 11 valid cases, got {summary.valid_cases}.")
    require(summary.invalid_cases >= 3, f"Expected at least 3 invalid stress cases, got {summary.invalid_cases}.")
    require("REQUIRE_REVIEW" in summary.decision_counts, "Suite never produced REQUIRE_REVIEW.")
    add_check(
        checks,
        "scenario-suite",
        True,
        f"{summary.total_cases} cases, {summary.valid_cases} valid, {summary.invalid_cases} invalid stress cases.",
    )


def validate_robustness_bundles(checks: list[ReleaseValidationCheck]) -> None:
    rules = read_rule_file(DEFAULT_RULES)
    fragile = read_scenario(FRAGILE_SCENARIO)
    fragile_bundle = build_robustness_visualization_bundle(fragile, rules, sample_override=20)
    require(fragile_bundle.nominal_replay.decision.value == "ALLOW", "Fragile scenario should be nominally allowed.")
    require(fragile_bundle.stress_replay is not None, "Fragile scenario should include stress replay.")
    require(
        fragile_bundle.robustness_report.monte_carlo.failure_probability > 0.0,
        "Fragile scenario should have nonzero uncertainty risk.",
    )

    repair = read_scenario(REPAIR_SCENARIO)
    repair_bundle = build_robustness_visualization_bundle(
        repair,
        rules,
        sample_override=20,
        compare_repair=True,
    )
    comparison = repair_bundle.robustness_report.repair_comparison
    require(comparison is not None, "Repair scenario should include repair comparison.")
    require(comparison.repair_available is True, "Buffered repair should be available.")
    require(comparison.repaired_failure_probability == 0.0, "Buffered repair should reach zero failure probability in validation sample.")
    require(repair_bundle.buffered_repair_replay is not None, "Repair bundle should include buffered repair replay.")

    add_check(
        checks,
        "robustness-bundles",
        True,
        "Fragile stress bundle and buffered repair bundle validated.",
    )


def validate_experiment_runs(checks: list[ReleaseValidationCheck]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        manifest = run_experiment(
            REPAIR_SCENARIO,
            DEFAULT_RULES,
            output_root=Path(temp_dir),
            experiment_id="release-validation-experiment",
            robustness=True,
            robustness_samples=20,
            compare_repair=True,
            tags=["release-validation"],
        )
        run_dir = Path(temp_dir) / "release-validation-experiment"
        require((run_dir / "manifest.json").exists(), "Experiment manifest missing.")
        require((run_dir / "summary.md").exists(), "Experiment summary missing.")
        require((run_dir / "evidence.json").exists(), "Experiment evidence missing.")
        require((run_dir / "replay.json").exists(), "Experiment replay missing.")
        require((run_dir / "robustness_bundle.json").exists(), "Experiment robustness bundle missing.")
        require(manifest.scenario_sha256, "Experiment manifest missing scenario hash.")
        require(manifest.rule_catalog_sha256, "Experiment manifest missing rule catalog hash.")

    add_check(checks, "experiment-run", True, "Experiment artifacts and provenance hashes validated.")


def validate_theater_contracts(checks: list[ReleaseValidationCheck]) -> None:
    required_tokens = {
        "index.html": ["scene-root", "replay-path-line", "ghost-repair-path-line", "WebGLRenderer"],
        "robustness.html": [
            "Robustness Theater",
            "nominal-replay-path",
            "stress-replay-path",
            "buffered-repair-replay-path",
            "failure_probability",
        ],
    }
    for path in THEATER_FILES:
        text = path.read_text(encoding="utf-8")
        for token in required_tokens[path.name]:
            require(token in text, f"{path.name} missing required token: {token}")
    add_check(checks, "theater-contracts", True, "Replay and robustness Theater static contracts validated.")


def run_release_validation() -> ReleaseValidationReport:
    checks: list[ReleaseValidationCheck] = []
    validate_suite(checks)
    validate_robustness_bundles(checks)
    validate_experiment_runs(checks)
    validate_theater_contracts(checks)
    return ReleaseValidationReport(passed=all(check.passed for check in checks), checks=checks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ORACLE-Omega release validation gates.")
    parser.add_argument("--out", type=Path, default=None, help="Optional output path for validation report JSON.")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    report = run_release_validation()
    payload = json.dumps(report.model_dump(mode="json"), indent=args.indent)
    print(payload)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    if not report.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
