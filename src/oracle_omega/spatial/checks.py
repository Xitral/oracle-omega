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
