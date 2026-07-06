from src.oracle_omega.core.models import PathSample, Vec3
from src.oracle_omega.spatial.checks import (
    max_lateral_offset,
    max_segment_speed,
    max_tilt,
    path_inside_radius,
)


def test_path_inside_radius_detects_entry():
    path = [
        PathSample(t=0, position=Vec3(x=5, y=0, z=0)),
        PathSample(t=1, position=Vec3(x=1, y=0, z=0)),
    ]

    inside, event_time, value = path_inside_radius(path, center=Vec3(x=0, y=0, z=0), radius=2)

    assert inside is True
    assert event_time == 1
    assert value == 1


def test_max_tilt_returns_largest_roll_or_pitch():
    path = [
        PathSample(t=0, position=Vec3(x=0, y=0, z=0), attitude_deg=Vec3(x=1, y=2, z=0)),
        PathSample(t=1, position=Vec3(x=0, y=0, z=0), attitude_deg=Vec3(x=9, y=3, z=0)),
    ]

    value, event_time = max_tilt(path)

    assert value == 9
    assert event_time == 1


def test_max_lateral_offset_uses_yz_plane():
    path = [
        PathSample(t=0, position=Vec3(x=10, y=0, z=0)),
        PathSample(t=1, position=Vec3(x=8, y=3, z=4)),
    ]

    value, event_time = max_lateral_offset(path)

    assert value == 5
    assert event_time == 1


def test_max_segment_speed_uses_position_delta_over_time():
    path = [
        PathSample(t=0, position=Vec3(x=0, y=0, z=0)),
        PathSample(t=2, position=Vec3(x=6, y=8, z=0)),
    ]

    value, event_time = max_segment_speed(path)

    assert value == 5
    assert event_time == 2
