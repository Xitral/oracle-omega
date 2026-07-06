from __future__ import annotations

from collections import Counter
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.oracle_omega.core.models import Decision, EvidenceCard
from src.oracle_omega.reviewer import review
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario


class SuiteCaseResult(BaseModel):
    path: str
    scenario_id: str | None = None
    scenario_family: str | None = None
    decision: Decision | None = None
    failed_count: int | None = None
    highest_severity: str | None = None
    primary_rule_id: str | None = None
    primary_violation_time: float | None = None
    valid: bool = True
    error: str | None = None


class SuiteSummary(BaseModel):
    suite_root: str
    total_cases: int
    valid_cases: int
    invalid_cases: int
    decision_counts: dict[str, int] = Field(default_factory=dict)
    severity_counts: dict[str, int] = Field(default_factory=dict)
    family_counts: dict[str, int] = Field(default_factory=dict)
    primary_rule_counts: dict[str, int] = Field(default_factory=dict)
    cases: list[SuiteCaseResult]


def scenario_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.yaml") if path.is_file())


def summarize_case(path: Path, evidence: EvidenceCard) -> SuiteCaseResult:
    return SuiteCaseResult(
        path=str(path),
        scenario_id=evidence.scenario_id,
        scenario_family=evidence.scenario_family,
        decision=evidence.decision,
        failed_count=evidence.failed_count,
        highest_severity=evidence.highest_severity,
        primary_rule_id=evidence.primary_rule_id,
        primary_violation_time=evidence.primary_violation_time,
        valid=True,
    )


def run_suite(suite_root: str | Path, rule_path: str | Path) -> SuiteSummary:
    root = Path(suite_root)
    rules = read_rule_file(rule_path)
    cases: list[SuiteCaseResult] = []

    for path in scenario_files(root):
        try:
            scenario = read_scenario(path)
            evidence = review(scenario, rules)
            cases.append(summarize_case(path, evidence))
        except Exception as exc:  # noqa: BLE001 - suite runner captures invalid research fixtures.
            cases.append(SuiteCaseResult(path=str(path), valid=False, error=str(exc)))

    valid_cases = [case for case in cases if case.valid]
    invalid_cases = [case for case in cases if not case.valid]

    return SuiteSummary(
        suite_root=str(root),
        total_cases=len(cases),
        valid_cases=len(valid_cases),
        invalid_cases=len(invalid_cases),
        decision_counts=count_field(valid_cases, "decision"),
        severity_counts=count_field(valid_cases, "highest_severity"),
        family_counts=count_field(valid_cases, "scenario_family"),
        primary_rule_counts=count_field(valid_cases, "primary_rule_id"),
        cases=cases,
    )


def normalized_counter_key(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def count_field(cases: list[SuiteCaseResult], field_name: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for case in cases:
        value: Any = getattr(case, field_name)
        if value is None:
            continue
        counter[normalized_counter_key(value)] += 1
    return dict(sorted(counter.items()))
