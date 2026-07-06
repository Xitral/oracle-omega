import json
from pathlib import Path

from src.oracle_omega.experiment import file_sha256, run_experiment

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "oracle" / "rules" / "starter_rules.yaml"
FRAGILE_CASE = ROOT / "oracle" / "scenarios" / "close_approach" / "fragile_corridor_pass.yaml"
REVIEW_CASE = ROOT / "oracle" / "scenarios" / "example_corridor_speed_review.yaml"


def test_experiment_run_writes_nominal_artifacts(tmp_path: Path):
    manifest = run_experiment(
        FRAGILE_CASE,
        RULES,
        output_root=tmp_path,
        experiment_id="fragile-test-run",
        tags=["unit-test", "fragile"],
    )

    run_dir = tmp_path / "fragile-test-run"
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "summary.md").exists()
    assert (run_dir / "evidence.json").exists()
    assert (run_dir / "replay.json").exists()
    assert not (run_dir / "robustness_bundle.json").exists()

    assert manifest.experiment_id == "fragile-test-run"
    assert manifest.scenario_sha256 == file_sha256(FRAGILE_CASE)
    assert manifest.rule_catalog_sha256 == file_sha256(RULES)
    assert manifest.decision == "ALLOW"
    assert manifest.robustness_enabled is False
    assert manifest.tags == ["unit-test", "fragile"]

    saved_manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert saved_manifest["artifacts"]["evidence"] == "evidence.json"
    assert saved_manifest["artifacts"]["replay"] == "replay.json"

    summary = (run_dir / "summary.md").read_text(encoding="utf-8")
    assert "ORACLE-Omega Experiment" in summary
    assert "Scenario SHA-256" in summary
    assert "Nominal review" in summary


def test_experiment_run_can_include_robustness_bundle(tmp_path: Path):
    manifest = run_experiment(
        REVIEW_CASE,
        RULES,
        output_root=tmp_path,
        experiment_id="repair-robustness-test-run",
        robustness=True,
        robustness_samples=10,
        compare_repair=True,
    )

    run_dir = tmp_path / "repair-robustness-test-run"
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "summary.md").exists()
    assert (run_dir / "evidence.json").exists()
    assert (run_dir / "replay.json").exists()
    assert (run_dir / "robustness_bundle.json").exists()

    assert manifest.decision == "REQUIRE_REVIEW"
    assert manifest.robustness_enabled is True
    assert manifest.robustness_samples == 10
    assert manifest.repair_comparison_enabled is True
    assert manifest.artifacts.robustness_bundle == "robustness_bundle.json"

    bundle = json.loads((run_dir / "robustness_bundle.json").read_text(encoding="utf-8"))
    assert bundle["robustness_report"]["repair_comparison"]["repaired_failure_probability"] == 0.0
    assert bundle["buffered_repair_replay"]["decision"] == "ALLOW"
