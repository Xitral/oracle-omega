from __future__ import annotations

import math

from src.oracle_omega.core.models import PathSample, Vec3


def subtract(a: Vec3, b: Vec3) -> Vec3:
    return Vec3(x=a.x - b.x, y=a.y - b.y, z=a.z - b.z)


def scale(value: Vec3, factor: float) -> Vec3:
    return Vec3(x=value.x * factor, y=value.y * factor, z=value.z * factor)


def norm(value: Vec3) -> float:
    return math.sqrt(value.x**2 + value.y**2 + value.z**2)


def segment_velocity(previous: PathSample, current: PathSample) -> Vec3 | None:
    dt = current.t - previous.t
    if dt <= 0:
        return None
    return scale(subtract(current.position, previous.position), 1.0 / dt)


def segment_velocities(path: list[PathSample]) -> list[tuple[float, Vec3]]:
    velocities: list[tuple[float, Vec3]] = []
    for previous, current in zip(path, path[1:]):
        velocity = segment_velocity(previous, current)
        if velocity is None:
            continue
        midpoint_time = previous.t + (current.t - previous.t) * 0.5
        velocities.append((midpoint_time, velocity))
    return velocities


def max_segment_acceleration(path: list[PathSample]) -> tuple[float, float | None]:
    velocities = segment_velocities(path)
    if len(velocities) < 2:
        return 0.0, None

    result = 0.0
    result_time = None
    for (previous_time, previous_velocity), (current_time, current_velocity) in zip(velocities, velocities[1:]):
        dt = current_time - previous_time
        if dt <= 0:
            continue
        value = norm(subtract(current_velocity, previous_velocity)) / dt
        if value > result:
            result = value
            result_time = current_time
    return result, result_time
