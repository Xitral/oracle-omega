from __future__ import annotations

import math

from src.oracle_omega.core.models import PathSample, Vec3


def distance(a: Vec3, b: Vec3) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


def path_inside_radius(path: list[PathSample], center: Vec3, radius: float) -> tuple[bool, float | None, float | None]:
    closest_value = None
    closest_time = None

    for sample in path:
        value = distance(sample.position, center)
        if closest_value is None or value < closest_value:
            closest_value = value
            closest_time = sample.t
        if value <= radius:
            return True, sample.t, value

    return False, closest_time, closest_value


def max_tilt(path: list[PathSample]) -> tuple[float, float | None]:
    result = 0.0
    result_time = None

    for sample in path:
        value = max(abs(sample.attitude_deg.x), abs(sample.attitude_deg.y))
        if value > result:
            result = value
            result_time = sample.t

    return result, result_time


def lateral_offset_yz(sample: PathSample) -> float:
    return math.sqrt(sample.position.y**2 + sample.position.z**2)


def max_lateral_offset(path: list[PathSample]) -> tuple[float, float | None]:
    result = 0.0
    result_time = None

    for sample in path:
        value = lateral_offset_yz(sample)
        if value > result:
            result = value
            result_time = sample.t

    return result, result_time


def max_segment_speed(path: list[PathSample]) -> tuple[float, float | None]:
    result = 0.0
    result_time = None

    for previous, current in zip(path, path[1:]):
        dt = current.t - previous.t
        if dt <= 0:
            continue
        value = distance(previous.position, current.position) / dt
        if value > result:
            result = value
            result_time = current.t

    return result, result_time
