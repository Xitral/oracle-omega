from __future__ import annotations

from pathlib import Path
from typing import Any

from src.oracle_omega.io_helpers import read_mapping


def read_rule_file(path: str | Path) -> list[dict[str, Any]]:
    data = read_mapping(path)
    items = data.get("rules")
    if not isinstance(items, list):
        raise ValueError(f"Expected rule list in {path}")
    return items
