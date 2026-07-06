from __future__ import annotations

from pathlib import Path

from src.oracle_omega.core.models import Scenario
from src.oracle_omega.io_helpers import read_mapping


def read_scenario(path: str | Path) -> Scenario:
    data = read_mapping(path)
    return Scenario.model_validate(data)
