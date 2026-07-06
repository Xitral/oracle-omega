from __future__ import annotations

import math
from typing import Any

from src.oracle_omega.core.models import EvidenceCard, RepairCandidate, Scenario, Vec3
from src.oracle_omega.repair import failed_rule_ids, path_delta_score
from src.oracle_omega.reviewer import applies_to_family, review
from src.oracle_omega.spatial.checks import distance

BUFFERED_REPAIR_STRATEGY = "uncertainty_buffered_repair_v1"
SIGMA_BUFFER = 3.0
EPSILON = 1e-6


def applicable_rules(rule_items: list[dict], scenario: Scenario) -> list[dict]:
    return [item for item in rule_items if applies_to_family(item, scenario.family)]


def first_rule(rule_items: list[dict], rule_type: str) -> dict | None:
    return next((item for item in rule_items if item.get("type") == rule_type), None)


def raw_uncertainty(scenario: Scenario) -> dict[str, Any]:
    value = scenario.parameters.get("uncertainty", {})
    return value if isinstance(value, dict) else {}


def sigma_vec(scenario: Scenario, key: str) -> Vec3:
    raw = raw_uncertainty(scenario).get(key, {})
    if not isinstance(raw, dict):
        return Vec3(x=0.0, y=0.0, z=0.0)
    return Vec3(x=float(raw.get("x", 0.0)), y=float(raw.get("y", 0.0)), z=float(raw.get("z", 0.0)))


def lateral_sigma(scenario: Scenario) -> float:
    sigma = sigma_vec(scenario, "position_sigma")
    return math.sqrt(sigma.y**2 + sigma.z**2)


def time_sigma(scenario: Scenario) -> float:
    return float(raw_uncertainty(scenario).get("timing_sigma", 0.0))


def copy_for_buffered_repair(scenario: Scenario) -> Scenario:
    return Scenario(
        id=f"{scenario.id}-buffered-repair",
        name=f"{scenario.name} Buffered Repair Candidate",
        family=scenario.family,
        planned_path=[sample.model_copy(deep=True) for sample in scenario.planned_path],
        parameters={**scenario.parameters, "repair_strategy": BUFFERED_REPAIR_STRATEGY},
    )


def corridor_target(max_offset: float, sigma: float) -> float:
    return min(max_offset * 0.85, max(max_offset * 0.25, max_offset - SIGMA_BUFFER * sigma))


def speed_target(max_speed: float) -> float:
    return max_speed * 0.72


def clearance_target(radius: float, sigma: float) -> float:
    return radius + radius * 0.1 + SIGMA_BUFFER * sigma


def clamp_corridor_with_buffer(scenario: Scenario, max_offset: float, sigma: float) -> None:
    target = corridor_target(max_offset, sigma)
    for sample in scenario.planned_path:
        lateral = math.sqrt(sample.position.y**2 + sample.position.z**2)
        if lateral <= target or lateral <= EPSILON:
            continue
        scale = target / lateral
        sample.position.y *= scale
        sample.position.z *= scale


def push_clearance_with_buffer(scenario: Scenario, center: Vec3, radius: float, sigma: float) -> None:
    target = clearance_target(radius, sigma)
    for sample in scenario.planned_path:
        value = distance(sample.position, center)
        if value >= target:
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


def retime_speed_with_buffer(scenario: Scenario, max_speed: float, sigma_t: float) -> None:
    if len(scenario.planned_path) < 2:
        return
    target = speed_target(max_speed)
    padding = SIGMA_BUFFER * sigma_t
    scenario.planned_path[0].t = 0.0
    for previous, current in zip(scenario.planned_path, scenario.planned_path[1:]):
        segment_distance = distance(previous.position, current.position)
        required_dt = segment_distance / target if segment_distance > 0 else 0.001
        original_dt = max(current.t - previous.t, 0.001)
        current.t = previous.t + max(original_dt, required_dt + padding)


def apply_buffered_repair(scenario: Scenario, rule_items: list[dict]) -> Scenario:
    repaired = copy_for_buffered_repair(scenario)
    rules = applicable_rules(rule_items, repaired)
    sigma = lateral_sigma(scenario)

    radius_rule = first_rule(rules, "radius_clearance")
    if radius_rule is not None:
        center = radius_rule["center"]
        push_clearance_with_buffer(
            repaired,
            Vec3(x=float(center["x"]), y=float(center["y"]), z=float(center["z"])),
            float(radius_rule["radius"]),
            sigma,
        )

    corridor_rule = first_rule(rules, "corridor_limit")
    if corridor_rule is not None:
        clamp_corridor_with_buffer(repaired, float(corridor_rule["max_offset"]), sigma)

    speed_rule = first_rule(rules, "speed_limit")
    if speed_rule is not None:
        retime_speed_with_buffer(repaired, float(speed_rule["max_speed"]), time_sigma(scenario))

    return repaired


def build_buffered_repair_candidate(
    scenario: Scenario,
    rule_items: list[dict],
    original_evidence: EvidenceCard | None = None,
) -> RepairCandidate:
    original = original_evidence if original_evidence is not None else review(scenario, rule_items)
    if original.failed_count == 0:
        return RepairCandidate(
            available=False,
            strategy=BUFFERED_REPAIR_STRATEGY,
            fixed_rules=[],
            remaining_failures=[],
            original_failed_count=0,
            repaired_failed_count=0,
            original_highest_severity=original.highest_severity,
            repaired_highest_severity=original.highest_severity,
            path_delta_score=0.0,
            modified_frame_count=0,
        )

    repaired = apply_buffered_repair(scenario, rule_items)
    repaired_evidence = review(repaired, rule_items)
    original_failures = failed_rule_ids(original)
    repaired_failures = failed_rule_ids(repaired_evidence)
    delta, modified = path_delta_score(scenario, repaired)

    return RepairCandidate(
        available=True,
        strategy=BUFFERED_REPAIR_STRATEGY,
        fixed_rules=sorted(original_failures - repaired_failures),
        remaining_failures=sorted(repaired_failures),
        original_failed_count=original.failed_count,
        repaired_failed_count=repaired_evidence.failed_count,
        original_highest_severity=original.highest_severity,
        repaired_highest_severity=repaired_evidence.highest_severity,
        path_delta_score=delta,
        modified_frame_count=modified,
        repaired_scenario=repaired,
        repaired_evidence=repaired_evidence,
    )
