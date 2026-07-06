from __future__ import annotations

from pathlib import Path
from typing import Any


def read_rule_file(path: str | Path) -> list[dict[str, Any]]:
    return [
        {
            "id": "APPROACH-CLEARANCE-001",
            "type": "radius_clearance",
            "center": {"x": 0.0, "y": 0.0, "z": 0.0},
            "radius": 2.0,
            "reason": "Central radius check.",
        },
        {
            "id": "LANDING-TILT-001",
            "type": "tilt_limit",
            "max_deg": 8.0,
            "reason": "Tilt check.",
        },
        {
            "id": "PATH-CORRIDOR-001",
            "type": "corridor_limit",
            "max_offset": 2.5,
            "reason": "Path corridor offset check.",
        },
        {
            "id": "PATH-SPEED-001",
            "type": "speed_limit",
            "max_speed": 0.65,
            "reason": "Path segment speed check.",
        },
    ]
