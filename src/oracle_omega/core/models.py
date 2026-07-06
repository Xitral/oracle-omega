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
    recommendation: str | None = None
    safety_margin: float | None = None
    normalized_margin: float | None = None
    severity: str = "nominal"


class EvidenceCard(BaseModel):
    scenario_id: str
    scenario_family: str
    decision: Decision
    results: list[RuleResult]
    checked_count: int
    failed_count: int
    primary_rule_id: str | None = None
    primary_violation_time: float | None = None
    primary_recommendation: str | None = None
    highest_severity: str = "nominal"
    summary: str


class ReplayMarker(BaseModel):
    rule_id: str
    t: float
    label: str
    severity: str = "review"
    recommendation: str | None = None
    safety_margin: float | None = None
    normalized_margin: float | None = None


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
    primary_recommendation: str | None = None
    highest_severity: str = "nominal"
    frames: list[ReplayFrame]


class RepairCandidate(BaseModel):
    available: bool
    strategy: str
    fixed_rules: list[str] = Field(default_factory=list)
    remaining_failures: list[str] = Field(default_factory=list)
    original_failed_count: int
    repaired_failed_count: int
    original_highest_severity: str
    repaired_highest_severity: str
    path_delta_score: float
    modified_frame_count: int
    repaired_scenario: Scenario | None = None
    repaired_evidence: EvidenceCard | None = None


class CounterfactualReplayBundle(BaseModel):
    scenario_id: str
    strategy: str
    repair_candidate: RepairCandidate
    original_replay: ReplayBundle
    repaired_replay: ReplayBundle | None = None


class UncertaintyConfig(BaseModel):
    position_sigma: Vec3 = Field(default_factory=lambda: Vec3(x=0.0, y=0.15, z=0.05))
    timing_sigma: float = 0.1
    attitude_sigma_deg: Vec3 = Field(default_factory=lambda: Vec3(x=0.5, y=0.5, z=0.25))
    samples: int = 100
    seed: int = 7


class MonteCarloSummary(BaseModel):
    sample_count: int
    pass_count: int
    fail_count: int
    failure_probability: float
    decision_counts: dict[str, int] = Field(default_factory=dict)
    failure_rule_counts: dict[str, int] = Field(default_factory=dict)
    severity_counts: dict[str, int] = Field(default_factory=dict)
    most_common_failure: str | None = None
    worst_case_severity: str = "nominal"


class AdversarialCase(BaseModel):
    found: bool
    triggered_rule: str | None = None
    perturbation_norm: float | None = None
    violation_time: float | None = None
    direction: dict[str, float] = Field(default_factory=dict)
    scenario: Scenario | None = None
    evidence: EvidenceCard | None = None
    description: str | None = None


class RobustnessReport(BaseModel):
    scenario_id: str
    scenario_family: str
    nominal_decision: Decision
    nominal_failed_count: int
    nominal_highest_severity: str
    uncertainty: UncertaintyConfig
    monte_carlo: MonteCarloSummary
    adversarial_case: AdversarialCase
