from pathlib import Path

from src.oracle_omega.core.models import Decision
from src.oracle_omega.repair import build_counterfactual_replay_bundle, build_repair_candidate
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario
from src.oracle_omega.reviewer import review

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "oracle" / "rules" / "starter_rules.yaml"
PASS_CASE = ROOT / "oracle" / "scenarios" / "example_path_pass.yaml"
REVIEW_CASE = ROOT / "oracle" / "scenarios" / "example_corridor_speed_review.yaml"


def test_repair_candidate_reduces_corridor_speed_failures():
    rules = read_rule_file(ITEMS)
    scenario = read_scenario(REVIEW_CASE)
    evidence = review(scenario, rules)

    repair = build_repair_candidate(scenario, rules, evidence)

    assert repair.available is True
    assert repair.original_failed_count == 2
    assert repair.repaired_failed_count < repair.original_failed_count
    assert "PATH-SPEED-001" in repair.fixed_rules
    assert "PATH-CORRIDOR-001" in repair.fixed_rules
    assert repair.path_delta_score > 0
    assert repair.modified_frame_count > 0
    assert repair.repaired_evidence is not None
    assert repair.repaired_evidence.decision == Decision.ALLOW


def test_repair_candidate_is_unavailable_for_nominal_case():
    rules = read_rule_file(ITEMS)
    scenario = read_scenario(PASS_CASE)
    evidence = review(scenario, rules)

    repair = build_repair_candidate(scenario, rules, evidence)

    assert repair.available is False
    assert repair.original_failed_count == 0
    assert repair.repaired_failed_count == 0
    assert repair.path_delta_score == 0
    assert repair.modified_frame_count == 0
    assert repair.repaired_scenario is None


def test_counterfactual_replay_bundle_includes_original_and_repaired_replays():
    rules = read_rule_file(ITEMS)
    scenario = read_scenario(REVIEW_CASE)

    bundle = build_counterfactual_replay_bundle(scenario, rules)

    assert bundle.scenario_id == "example-corridor-speed-review"
    assert bundle.repair_candidate.available is True
    assert bundle.original_replay.decision == Decision.REQUIRE_REVIEW
    assert bundle.repaired_replay is not None
    assert bundle.repaired_replay.decision == Decision.ALLOW
    assert len(bundle.original_replay.frames) == len(bundle.repaired_replay.frames)
