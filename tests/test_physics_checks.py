from src.oracle_omega.core.models import PathSample, Scenario, Vec3
from src.oracle_omega.physics.kinematics import max_segment_acceleration
from src.oracle_omega.reviewer import review


def accelerating_scenario() -> Scenario:
    return Scenario(
        id="physics-acceleration-demo",
        name="Physics acceleration demo",
        family="close_approach",
        planned_path=[
            PathSample(t=0.0, position=Vec3(x=0.0, y=0.0, z=0.0)),
            PathSample(t=1.0, position=Vec3(x=1.0, y=0.0, z=0.0)),
            PathSample(t=2.0, position=Vec3(x=10.0, y=0.0, z=0.0)),
        ],
    )


def test_max_segment_acceleration_uses_velocity_change_over_time():
    value, event_time = max_segment_acceleration(accelerating_scenario().planned_path)

    assert value == 8.0
    assert event_time == 1.5


def test_reviewer_reports_acceleration_limit_failure():
    evidence = review(
        accelerating_scenario(),
        [
            {
                "id": "PATH-ACCEL-TEST",
                "type": "acceleration_limit",
                "max_acceleration": 2.0,
                "reason": "Acceleration feasibility check.",
                "recommendation": "Smooth the path before accepting the scenario.",
            }
        ],
    )

    assert evidence.decision.value == "REQUIRE_REVIEW"
    assert evidence.failed_count == 1
    assert evidence.primary_rule_id == "PATH-ACCEL-TEST"
    result = evidence.results[0]
    assert result.measured["max_segment_acceleration"] == 8.0
    assert result.safety_margin == -6.0
