from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from pydantic import BaseModel, Field

from src.oracle_omega.core.models import Vec3

HORIZONS_ENDPOINT = "https://ssd.jpl.nasa.gov/api/horizons.api"
FLOAT_RE = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?"
JD_RE = re.compile(rf"^\s*({FLOAT_RE})\s*=\s*(.*?)\s*$")
COMPONENT_RE = re.compile(rf"\b([XYZ]|VX|VY|VZ)\s*=\s*({FLOAT_RE})")


class HorizonsQuery(BaseModel):
    command: str
    center: str
    start_time: str
    stop_time: str
    step_size: str
    ephem_type: str = "VECTORS"
    out_units: str = "KM-S"
    ref_system: str = "ICRF"
    vec_table: str = "2"
    format: str = "json"


class HorizonsVectorSample(BaseModel):
    jd: float
    calendar: str
    position_km: Vec3
    velocity_km_s: Vec3


class HorizonsVectorSeries(BaseModel):
    source: str = "JPL Horizons"
    command: str | None = None
    center: str | None = None
    samples: list[HorizonsVectorSample] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


def quote_horizons_value(value: str) -> str:
    if value.startswith("'") and value.endswith("'"):
        return value
    return f"'{value}'"


def build_horizons_params(query: HorizonsQuery) -> dict[str, str]:
    return {
        "format": query.format,
        "COMMAND": quote_horizons_value(query.command),
        "OBJ_DATA": "NO",
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": quote_horizons_value(query.ephem_type),
        "CENTER": quote_horizons_value(query.center),
        "START_TIME": quote_horizons_value(query.start_time),
        "STOP_TIME": quote_horizons_value(query.stop_time),
        "STEP_SIZE": quote_horizons_value(query.step_size),
        "OUT_UNITS": quote_horizons_value(query.out_units),
        "REF_SYSTEM": quote_horizons_value(query.ref_system),
        "VEC_TABLE": quote_horizons_value(query.vec_table),
    }


def build_horizons_url(query: HorizonsQuery, endpoint: str = HORIZONS_ENDPOINT) -> str:
    return f"{endpoint}?{urlencode(build_horizons_params(query))}"


def load_horizons_result(path: str | Path) -> str:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("result"), str):
        return data["result"]
    if isinstance(data, dict) and isinstance(data.get("text"), str):
        return data["text"]
    raise ValueError("Expected a Horizons JSON object with a string 'result' or 'text' field.")


def fetch_horizons_json(query: HorizonsQuery, endpoint: str = HORIZONS_ENDPOINT, timeout: float = 30.0) -> dict:
    url = build_horizons_url(query, endpoint=endpoint)
    with urlopen(url, timeout=timeout) as response:  # noqa: S310 - explicit CLI fetch for a known endpoint.
        payload = response.read().decode("utf-8")
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Expected Horizons response to decode to a JSON object.")
    return data


def complete_sample(raw: dict[str, float | str]) -> bool:
    required = {"jd", "calendar", "x", "y", "z", "vx", "vy", "vz"}
    return required <= set(raw)


def sample_from_raw(raw: dict[str, float | str]) -> HorizonsVectorSample:
    return HorizonsVectorSample(
        jd=float(raw["jd"]),
        calendar=str(raw["calendar"]),
        position_km=Vec3(x=float(raw["x"]), y=float(raw["y"]), z=float(raw["z"])),
        velocity_km_s=Vec3(x=float(raw["vx"]), y=float(raw["vy"]), z=float(raw["vz"])),
    )


def parse_horizons_vectors(
    text: str,
    command: str | None = None,
    center: str | None = None,
) -> HorizonsVectorSeries:
    in_table = False
    current: dict[str, float | str] = {}
    samples: list[HorizonsVectorSample] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "$$SOE":
            in_table = True
            continue
        if stripped == "$$EOE":
            if complete_sample(current):
                samples.append(sample_from_raw(current))
            break
        if not in_table:
            continue

        jd_match = JD_RE.match(line)
        if jd_match:
            if complete_sample(current):
                samples.append(sample_from_raw(current))
            current = {"jd": float(jd_match.group(1)), "calendar": jd_match.group(2).strip()}
            continue

        for name, value in COMPONENT_RE.findall(line):
            current[name.lower()] = float(value)

    if not samples:
        raise ValueError("No complete Horizons vector samples were found between $$SOE and $$EOE.")

    return HorizonsVectorSeries(command=command, center=center, samples=samples)


def parse_horizons_json(data: dict, command: str | None = None, center: str | None = None) -> HorizonsVectorSeries:
    result = data.get("result")
    if not isinstance(result, str):
        raise ValueError("Expected Horizons JSON response to include a string 'result' field.")
    return parse_horizons_vectors(result, command=command, center=center)
