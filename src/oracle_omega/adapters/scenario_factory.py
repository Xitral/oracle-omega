from __future__ import annotations

from pathlib import Path

import yaml

from src.oracle_omega.adapters.horizons import HorizonsVectorSeries
from src.oracle_omega.core.models import PathSample, Scenario, Vec3
from src.oracle_omega.scenario_validation import validate_scenario


def scaled_vec(value: Vec3, scale: float, origin: Vec3 | None = None) -> Vec3:
    base = origin if origin is not None else Vec3(x=0.0, y=0.0, z=0.0)
    return Vec3(
        x=(value.x - base.x) * scale,
        y=(value.y - base.y) * scale,
        z=(value.z - base.z) * scale,
    )


def sample_time_seconds(jd: float, first_jd: float) -> float:
    return (jd - first_jd) * 86400.0


def scenario_from_horizons_vectors(
    series: HorizonsVectorSeries,
    scenario_id: str,
    name: str,
    family: str = "close_approach",
    position_scale: float = 0.001,
    recenter: bool = False,
    max_samples: int | None = None,
) -> Scenario:
    if not series.samples:
        raise ValueError("Cannot build a scenario from an empty Horizons vector series.")

    selected = series.samples[:max_samples] if max_samples is not None else series.samples
    first = selected[0]
    origin = first.position_km if recenter else None
    path = [
        PathSample(
            t=sample_time_seconds(sample.jd, first.jd),
            position=scaled_vec(sample.position_km, position_scale, origin),
            attitude_deg=Vec3(x=0.0, y=0.0, z=0.0),
        )
        for sample in selected
    ]
    scenario = Scenario(
        id=scenario_id,
        name=name,
        family=family,
        planned_path=path,
        parameters={
            "external_source": "JPL Horizons",
            "source_command": series.command,
            "source_center": series.center,
            "position_scale": position_scale,
            "recentered_to_first_sample": recenter,
            "source_sample_count": len(series.samples),
        },
    )
    return validate_scenario(scenario)


def scenario_to_yaml(scenario: Scenario) -> str:
    return yaml.safe_dump(scenario.model_dump(mode="json"), sort_keys=False)


def write_scenario(scenario: Scenario, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(scenario_to_yaml(scenario), encoding="utf-8")
