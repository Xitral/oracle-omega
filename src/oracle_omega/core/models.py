from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Decision(str, Enum):
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
    scenario_family: str
    decision: Decision
    results: list[RuleResult]
    checked_count: int
    failed_count: int
    primary_rule_id: str | None = None
    primary_violation_time: float | None = None
    summary: str


class ReplayMarker(BaseModel):
    rule_id: str
    t: float
    label: str
    severity: str = "review"


class ReplayFrame(BaseModel):
    t: float
    position: Vec3
    attitude_deg: Vec3
    active_markers: list[ReplayMarker] = Field(default_factory=list)
    is_primary_violation_frame: bool = False


class ReplayBundle(BaseModel):
    scenario_id: str
    scenario_family: str
    decision: Decision
    primary_rule_id: str | None = None
    primary_violation_time: float | None = None
    frames: list[ReplayFrame]
