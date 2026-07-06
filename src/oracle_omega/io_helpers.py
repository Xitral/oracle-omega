from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def read_mapping(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {file_path}")
    return data
