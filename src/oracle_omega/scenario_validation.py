from __future__ import annotations

import math

from src.oracle_omega.core.models import PathSample, Scenario, Vec3

KNOWN_SCENARIO_FAMILIES = {"close_approach", "surface_landing"}


class ScenarioValidationError(ValueError):
    pass


def require_finite_vec3(value: Vec3, label: str) -> None:
    fields = {"x": value.x, "y": value.y, "z": value.z}
    for axis, number in fields.items():
        if not math.isfinite(number):
            raise ScenarioValidationError(f"{label}.{axis} must be finite.")


def validate_path_sample(sample: PathSample, index: int) -> None:
    if not math.isfinite(sample.t):
        raise ScenarioValidationError(f"planned_path[{index}].t must be finite.")
    require_finite_vec3(sample.position, f"planned_path[{index}].position")
    require_finite_vec3(sample.attitude_deg, f"planned_path[{index}].attitude_deg")


def validate_monotonic_time(path: list[PathSample]) -> None:
    previous = None
    for index, sample in enumerate(path):
        if previous is not None and sample.t <= previous:
            raise ScenarioValidationError(
                f"planned_path timestamps must be strictly increasing; "
                f"planned_path[{index}].t={sample.t} follows {previous}."
            )
        previous = sample.t


def validate_scenario(scenario: Scenario) -> Scenario:
    if scenario.family not in KNOWN_SCENARIO_FAMILIES:
        families = ", ".join(sorted(KNOWN_SCENARIO_FAMILIES))
        raise ScenarioValidationError(
            f"Unknown scenario family '{scenario.family}'. Expected one of: {families}."
        )

    if not scenario.planned_path:
        raise ScenarioValidationError("planned_path must contain at least one sample.")

    for index, sample in enumerate(scenario.planned_path):
        validate_path_sample(sample, index)

    validate_monotonic_time(scenario.planned_path)
    return scenario
