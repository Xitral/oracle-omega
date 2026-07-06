from __future__ import annotations

import math
from typing import Any

from src.oracle_omega.core.models import Scenario, Vec3
from src.oracle_omega.reviewer import applies_to_family
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
