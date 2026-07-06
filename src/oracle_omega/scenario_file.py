from __future__ import annotations

from pathlib import Path

import yaml

from src.oracle_omega.core.models import Scenario


def read_scenario(path: str | Path) -> Scenario:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return Scenario.model_validate(data)
