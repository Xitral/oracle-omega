from pathlib import Path

import pytest

from src.oracle_omega.rule_file import RuleCatalogError, read_rule_file

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "oracle" / "rules" / "starter_rules.yaml"


def test_read_rule_file_uses_yaml_contents(tmp_path: Path):
    path = tmp_path / "checks.yaml"
    path.write_text(
        "checks:\n"
        "  - id: CUSTOM-SPEED\n"
        "    type: speed_limit\n"
        "    families: [close_approach]\n"
        "    max_speed: 1.23\n"
        "    reason: Custom speed check.\n"
        "    recommendation: Slow down.\n",
        encoding="utf-8",
    )

    checks = read_rule_file(path)

    assert len(checks) == 1
    assert checks[0]["id"] == "CUSTOM-SPEED"
    assert checks[0]["max_speed"] == 1.23
    assert checks[0]["recommendation"] == "Slow down."


def test_starter_catalog_contains_expected_checks():
    checks = read_rule_file(ITEMS)
    ids = {item["id"] for item in checks}

    assert ids == {
        "APPROACH-CLEARANCE-001",
        "LANDING-TILT-001",
        "PATH-CORRIDOR-001",
        "PATH-SPEED-001",
    }
    assert next(item for item in checks if item["id"] == "PATH-SPEED-001")["max_speed"] == 0.65
    assert next(item for item in checks if item["id"] == "PATH-CORRIDOR-001")["max_offset"] == 2.5


def test_rule_file_rejects_missing_checks(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text("catalog_id: bad\n", encoding="utf-8")

    with pytest.raises(RuleCatalogError, match="checks"):
        read_rule_file(path)


def test_rule_file_rejects_duplicate_ids(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "checks:\n"
        "  - id: DUP\n"
        "    type: speed_limit\n"
        "    max_speed: 1.0\n"
        "    reason: One.\n"
        "  - id: DUP\n"
        "    type: speed_limit\n"
        "    max_speed: 2.0\n"
        "    reason: Two.\n",
        encoding="utf-8",
    )

    with pytest.raises(RuleCatalogError, match="Duplicate"):
        read_rule_file(path)


def test_rule_file_rejects_unsupported_type(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "checks:\n"
        "  - id: UNKNOWN\n"
        "    type: unknown_check\n"
        "    reason: Bad.\n",
        encoding="utf-8",
    )

    with pytest.raises(RuleCatalogError, match="Unsupported"):
        read_rule_file(path)


def test_rule_file_rejects_missing_required_type_field(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "checks:\n"
        "  - id: BAD-SPEED\n"
        "    type: speed_limit\n"
        "    reason: Missing speed.\n",
        encoding="utf-8",
    )

    with pytest.raises(RuleCatalogError, match="max_speed"):
        read_rule_file(path)
