from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Decision(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    HOLD = "HOLD"
    REPLAN = "REPLAN"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"


class Vec3(BaseModel):
    x: float
    y: float
    z: float


class PathSample(BaseModel):
    t: float = Field(description="Seconds from scenario start.")
    position: Vec3
    attitude_deg: Vec3 = Field(default_factory=lambda: Vec3(x=0.0, y=0.0, z=0.0))


class Scenario(BaseModel):
    id: str
    name: str
    family: str
    planned_path: list[PathSample]
    parameters: dict[str, Any] = Field(default_factory=dict)


class RuleResult(BaseModel):
    rule_id: str
    passed: bool
    measured: dict[str, Any] = Field(default_factory=dict)
    reason: str
    violation_time: float | None = None


class EvidenceCard(BaseModel):
    scenario_id: str
    decision: Decision
    results: list[RuleResult]
    summary: str
