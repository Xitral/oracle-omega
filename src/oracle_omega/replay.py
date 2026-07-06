from __future__ import annotations

from src.oracle_omega.core.models import (
    EvidenceCard,
    ReplayBundle,
    ReplayFrame,
    ReplayMarker,
    Scenario,
)


def markers_at_time(evidence: EvidenceCard, t: float) -> list[ReplayMarker]:
    markers: list[ReplayMarker] = []
    for result in evidence.results:
        if result.passed or result.violation_time is None:
            continue
        if result.violation_time == t:
            markers.append(
                ReplayMarker(
                    rule_id=result.rule_id,
                    t=t,
                    label=result.reason,
                    recommendation=result.recommendation,
                )
            )
    return markers


def build_replay_bundle(scenario: Scenario, evidence: EvidenceCard) -> ReplayBundle:
    frames: list[ReplayFrame] = []

    for sample in scenario.planned_path:
        markers = markers_at_time(evidence, sample.t)
        frames.append(
            ReplayFrame(
                t=sample.t,
                position=sample.position,
                attitude_deg=sample.attitude_deg,
                active_markers=markers,
                is_primary_violation_frame=(
                    evidence.primary_violation_time is not None
                    and sample.t == evidence.primary_violation_time
                ),
            )
        )

    return ReplayBundle(
        scenario_id=scenario.id,
        scenario_family=scenario.family,
        decision=evidence.decision,
        primary_rule_id=evidence.primary_rule_id,
        primary_violation_time=evidence.primary_violation_time,
        primary_recommendation=evidence.primary_recommendation,
        frames=frames,
    )
