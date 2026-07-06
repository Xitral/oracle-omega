from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SUPPORTED_CHECK_TYPES = {
    "radius_clearance",
    "tilt_limit",
    "corridor_limit",
    "speed_limit",
    "acceleration_limit",
}

REQUIRED_FIELDS_BY_TYPE = {
    "radius_clearance": {"id", "type", "center", "radius", "reason"},
    "tilt_limit": {"id", "type", "max_deg", "reason"},
    "corridor_limit": {"id", "type", "max_offset", "reason"},
    "speed_limit": {"id", "type", "max_speed", "reason"},
    "acceleration_limit": {"id", "type", "max_acceleration", "reason"},
}


class RuleCatalogError(ValueError):
    pass


def read_rule_file(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    checks = extract_checks(data, file_path)
    validate_check_catalog(checks, file_path)
    return checks


def extract_checks(data: Any, file_path: Path) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        raise RuleCatalogError(f"Expected a mapping in check catalog {file_path}.")

    checks = data.get("checks", data.get("rules"))
    if not isinstance(checks, list):
        raise RuleCatalogError(f"Expected 'checks' list in check catalog {file_path}.")

    result: list[dict[str, Any]] = []
    for index, item in enumerate(checks):
        if not isinstance(item, dict):
            raise RuleCatalogError(f"Check catalog item {index} in {file_path} must be a mapping.")
        result.append(item)
    return result


def validate_check_catalog(checks: list[dict[str, Any]], file_path: Path) -> None:
    seen_ids: set[str] = set()
    for index, item in enumerate(checks):
        check_id = require_string(item, "id", file_path, index)
        if check_id in seen_ids:
            raise RuleCatalogError(f"Duplicate check id '{check_id}' in {file_path}.")
        seen_ids.add(check_id)

        check_type = require_string(item, "type", file_path, index)
        if check_type not in SUPPORTED_CHECK_TYPES:
            supported = ", ".join(sorted(SUPPORTED_CHECK_TYPES))
            raise RuleCatalogError(
                f"Unsupported check type '{check_type}' for check '{check_id}' in {file_path}. "
                f"Expected one of: {supported}."
            )

        missing = REQUIRED_FIELDS_BY_TYPE[check_type] - set(item)
        if missing:
            fields = ", ".join(sorted(missing))
            raise RuleCatalogError(f"Check '{check_id}' in {file_path} is missing required fields: {fields}.")

        validate_families(item, file_path, index)
        validate_numeric_fields(item, file_path, index)
        validate_center(item, file_path, index)


def require_string(item: dict[str, Any], field: str, file_path: Path, index: int) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value:
        raise RuleCatalogError(f"Check catalog item {index} in {file_path} requires non-empty string field '{field}'.")
    return value


def validate_families(item: dict[str, Any], file_path: Path, index: int) -> None:
    families = item.get("families")
    if families is None:
        return
    if not isinstance(families, list) or not all(isinstance(value, str) and value for value in families):
        raise RuleCatalogError(f"Check catalog item {index} in {file_path} has invalid 'families'.")


def validate_numeric_fields(item: dict[str, Any], file_path: Path, index: int) -> None:
    for field in ("radius", "max_deg", "max_offset", "max_speed", "max_acceleration"):
        if field not in item:
            continue
        value = item[field]
        if not isinstance(value, int | float) or value <= 0:
            raise RuleCatalogError(f"Check catalog item {index} in {file_path} requires positive numeric '{field}'.")


def validate_center(item: dict[str, Any], file_path: Path, index: int) -> None:
    if item.get("type") != "radius_clearance":
        return
    center = item.get("center")
    if not isinstance(center, dict):
        raise RuleCatalogError(f"Check catalog item {index} in {file_path} requires center mapping.")
    for axis in ("x", "y", "z"):
        value = center.get(axis)
        if not isinstance(value, int | float):
            raise RuleCatalogError(f"Check catalog item {index} in {file_path} requires numeric center.{axis}.")
