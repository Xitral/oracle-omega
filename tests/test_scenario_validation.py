import math

import pytest

from src.oracle_omega.core.models import PathSample, Scenario, Vec3
from src.oracle_omega.scenario_validation import ScenarioValidationError, validate_scenario


def sample(t: float) -> PathSample:
    return PathSample(t=t, position=Vec3(x=1.0, y=0.0, z=0.0))


def test_validation_accepts_known_family_and_increasing_time():
    scenario = Scenario(
        id="valid",
        name="Valid Scenario",
        family="close_approach",
        planned_path=[sample(0.0), sample(1.0)],
    )

    assert validate_scenario(scenario) is scenario


def test_validation_rejects_unknown_family():
    scenario = Scenario(
        id="bad-family",
        name="Bad Family",
        family="unknown_family",
        planned_path=[sample(0.0)],
    )

    with pytest.raises(ScenarioValidationError, match="Unknown scenario family"):
        validate_scenario(scenario)


def test_validation_rejects_empty_path():
    scenario = Scenario(
        id="empty",
        name="Empty Path",
        family="close_approach",
        planned_path=[],
    )

    with pytest.raises(ScenarioValidationError, match="planned_path must contain"):
        validate_scenario(scenario)


def test_validation_rejects_non_increasing_timestamps():
    scenario = Scenario(
        id="bad-time",
        name="Bad Time",
        family="close_approach",
        planned_path=[sample(1.0), sample(1.0)],
    )

    with pytest.raises(ScenarioValidationError, match="strictly increasing"):
        validate_scenario(scenario)


def test_validation_rejects_non_finite_values():
    scenario = Scenario(
        id="bad-value",
        name="Bad Value",
        family="close_approach",
        planned_path=[PathSample(t=0.0, position=Vec3(x=math.inf, y=0.0, z=0.0))],
    )

    with pytest.raises(ScenarioValidationError, match="must be finite"):
        validate_scenario(scenario)
