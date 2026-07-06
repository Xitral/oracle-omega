from pathlib import Path

from src.oracle_omega.replay import build_replay_bundle
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario
from src.oracle_omega.reviewer import review

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "oracle" / "rules" / "starter_rules.yaml"
CASE_C = ROOT / "oracle" / "scenarios" / "example_corridor_speed_review.yaml"


def test_replay_bundle_marks_primary_violation_frame():
    scenario = read_scenario(CASE_C)
    evidence = review(scenario, read_rule_file(ITEMS))

    replay = build_replay_bundle(scenario, evidence)

    assert replay.scenario_id == "example-corridor-speed-review"
    assert replay.scenario_family == "close_approach"
    assert replay.primary_rule_id == "PATH-SPEED-001"
    assert replay.primary_violation_time == 5.0
    assert len(replay.frames) == len(scenario.planned_path)

    primary_frames = [frame for frame in replay.frames if frame.is_primary_violation_frame]
    assert len(primary_frames) == 1
    assert primary_frames[0].t == 5.0
    assert {marker.rule_id for marker in primary_frames[0].active_markers} == {"PATH-SPEED-001"}


def test_replay_bundle_marks_later_non_primary_violation():
    scenario = read_scenario(CASE_C)
    evidence = review(scenario, read_rule_file(ITEMS))

    replay = build_replay_bundle(scenario, evidence)
    frame_at_ten = next(frame for frame in replay.frames if frame.t == 10.0)

    assert frame_at_ten.is_primary_violation_frame is False
    assert {marker.rule_id for marker in frame_at_ten.active_markers} == {"PATH-CORRIDOR-001"}
