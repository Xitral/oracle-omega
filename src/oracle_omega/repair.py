from __future__ import annotations

import math

from src.oracle_omega.core.models import (
    CounterfactualReplayBundle,
    EvidenceCard,
    PathSample,
    RepairCandidate,
    ReplayBundle,
    Scenario,
    Vec3,
)
from src.oracle_omega.replay import build_replay_bundle
from src.oracle_omega.reviewer import applies_to_family, review
from src.oracle_omega.spatial.checks import distance

REPAIR_STRATEGY = "counterfactual_minimal_path_change_v1"
EPSILON = 1e-6


def failed_rule_ids(evidence: EvidenceCard) -> set[str]:
    return {result.rule_id for result in evidence.results if not result.passed}


def copy_sample(sample: PathSample) -> PathSample:
    return PathSample(
        t=sample.t,
        position=Vec3(x=sample.position.x, y=sample.position.y, z=sample.position.z),
        attitude_deg=Vec3(
            x=sample.attitude_deg.x,
            y=sample.attitude_deg.y,
            z=sample.attitude_deg.z,
        ),
    )


def copy_scenario(scenario: Scenario) -> Scenario:
    return Scenario(
        id=f"{scenario.id}-repair",
        name=f"{scenario.name} Repair Candidate",
        family=scenario.family,
        planned_path=[copy_sample(sample) for sample in scenario.planned_path],
        parameters={**scenario.parameters, "repair_strategy": REPAIR_STRATEGY},
    )


def applicable_rules(rule_items: list[dict], scenario: Scenario) -> list[dict]:
    return [item for item in rule_items if applies_to_family(item, scenario.family)]


def first_rule(rule_items: list[dict], rule_type: str) -> dict | None:
    return next((item for item in rule_items if item.get("type") == rule_type), None)


def clamp_lateral_corridor(scenario: Scenario, max_offset: float) -> None:
    target = max_offset * 0.96
    for sample in scenario.planned_path:
        lateral = math.sqrt(sample.position.y**2 + sample.position.z**2)
        if lateral <= max_offset or lateral <= EPSILON:
            continue
        scale = target / lateral
        sample.position.y *= scale
        sample.position.z *= scale


def push_outside_radius(scenario: Scenario, center: Vec3, radius: float) -> None:
    target = radius * 1.08
    for sample in scenario.planned_path:
        value = distance(sample.position, center)
        if value > radius:
            continue
        if value <= EPSILON:
            sample.position.x = center.x + target
            sample.position.y = center.y
            sample.position.z = center.z
            continue
        scale = target / value
        sample.position.x = center.x + (sample.position.x - center.x) * scale
        sample.position.y = center.y + (sample.position.y - center.y) * scale
        sample.position.z = center.z + (sample.position.z - center.z) * scale


def clamp_tilt(scenario: Scenario, max_deg: float) -> None:
    target = max_deg * 0.96
    for sample in scenario.planned_path:
        sample.attitude_deg.x = max(-target, min(target, sample.attitude_deg.x))
        sample.attitude_deg.y = max(-target, min(target, sample.attitude_deg.y))


def retime_for_speed(scenario: Scenario, max_speed: float) -> None:
    if len(scenario.planned_path) < 2 or max_speed <= 0:
        return

    repaired = scenario.planned_path
    repaired[0].t = 0.0
    for previous, current in zip(repaired, repaired[1:]):
        segment_distance = distance(previous.position, current.position)
        minimum_dt = segment_distance / max_speed if segment_distance > 0 else 0.001
        original_dt = max(current.t - previous.t, 0.001)
        current.t = previous.t + max(original_dt, minimum_dt * 1.04)


def apply_repairs(scenario: Scenario, rule_items: list[dict]) -> Scenario:
    repaired = copy_scenario(scenario)
    rules = applicable_rules(rule_items, repaired)

    radius_rule = first_rule(rules, "radius_clearance")
    if radius_rule is not None:
        center_data = radius_rule["center"]
        push_outside_radius(
            repaired,
            Vec3(x=float(center_data["x"]), y=float(center_data["y"]), z=float(center_data["z"])),
            float(radius_rule["radius"]),
        )

    corridor_rule = first_rule(rules, "corridor_limit")
    if corridor_rule is not None:
        clamp_lateral_corridor(repaired, float(corridor_rule["max_offset"]))

    tilt_rule = first_rule(rules, "tilt_limit")
    if tilt_rule is not None:
        clamp_tilt(repaired, float(tilt_rule["max_deg"]))

    speed_rule = first_rule(rules, "speed_limit")
    if speed_rule is not None:
        retime_for_speed(repaired, float(speed_rule["max_speed"]))

    return repaired


def path_delta_score(original: Scenario, repaired: Scenario) -> tuple[float, int]:
    if not original.planned_path:
        return 0.0, 0

    total = 0.0
    modified = 0
    for before, after in zip(original.planned_path, repaired.planned_path):
        position_delta = distance(before.position, after.position)
        attitude_delta = max(
            abs(before.attitude_deg.x - after.attitude_deg.x),
            abs(before.attitude_deg.y - after.attitude_deg.y),
            abs(before.attitude_deg.z - after.attitude_deg.z),
        ) / 90.0
        time_delta = abs(before.t - after.t) / max(before.t + 1.0, 1.0)
        frame_delta = position_delta + attitude_delta + time_delta
        total += frame_delta
        if frame_delta > EPSILON:
            modified += 1

    return total / len(original.planned_path), modified


def build_repair_candidate(
    scenario: Scenario,
    rule_items: list[dict],
    original_evidence: EvidenceCard | None = None,
) -> RepairCandidate:
    original = original_evidence if original_evidence is not None else review(scenario, rule_items)

    if original.failed_count == 0:
        return RepairCandidate(
            available=False,
            strategy=REPAIR_STRATEGY,
            fixed_rules=[],
            remaining_failures=[],
            original_failed_count=0,
            repaired_failed_count=0,
            original_highest_severity=original.highest_severity,
            repaired_highest_severity=original.highest_severity,
            path_delta_score=0.0,
            modified_frame_count=0,
            repaired_scenario=None,
            repaired_evidence=None,
        )

    repaired_scenario = apply_repairs(scenario, rule_items)
    repaired_evidence = review(repaired_scenario, rule_items)
    original_failures = failed_rule_ids(original)
    repaired_failures = failed_rule_ids(repaired_evidence)
    delta_score, modified_count = path_delta_score(scenario, repaired_scenario)

    return RepairCandidate(
        available=True,
        strategy=REPAIR_STRATEGY,
        fixed_rules=sorted(original_failures - repaired_failures),
        remaining_failures=sorted(repaired_failures),
        original_failed_count=original.failed_count,
        repaired_failed_count=repaired_evidence.failed_count,
        original_highest_severity=original.highest_severity,
        repaired_highest_severity=repaired_evidence.highest_severity,
        path_delta_score=delta_score,
        modified_frame_count=modified_count,
        repaired_scenario=repaired_scenario,
        repaired_evidence=repaired_evidence,
    )


def build_counterfactual_replay_bundle(
    scenario: Scenario,
    rule_items: list[dict],
    original_evidence: EvidenceCard | None = None,
    original_replay: ReplayBundle | None = None,
) -> CounterfactualReplayBundle:
    evidence = original_evidence if original_evidence is not None else review(scenario, rule_items)
    replay = original_replay if original_replay is not None else build_replay_bundle(scenario, evidence)
    repair = build_repair_candidate(scenario, rule_items, evidence)

    repaired_replay = None
    if repair.available and repair.repaired_scenario is not None and repair.repaired_evidence is not None:
        repaired_replay = build_replay_bundle(repair.repaired_scenario, repair.repaired_evidence)

    return CounterfactualReplayBundle(
        scenario_id=scenario.id,
        strategy=REPAIR_STRATEGY,
        repair_candidate=repair,
        original_replay=replay,
        repaired_replay=repaired_replay,
    )
