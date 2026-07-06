from __future__ import annotations

from typing import Any

from src.oracle_omega.core.models import Decision, EvidenceCard, RuleResult, Scenario, Vec3
from src.oracle_omega.spatial.checks import (
    max_lateral_offset,
    max_segment_speed,
    max_tilt,
    path_inside_radius,
)

SEVERITY_RANK = {"nominal": 0, "review": 1, "critical": 2}


def applies_to_family(item: dict[str, Any], family: str) -> bool:
    families = item.get("families")
    if families is None:
        return True
    return family in families


def recommendation_for(item: dict[str, Any]) -> str | None:
    value = item.get("recommendation")
    return None if value is None else str(value)


def normalized_margin(margin: float, limit: float) -> float:
    if limit == 0:
        return 0.0
    return margin / abs(limit)


def severity_for(passed: bool, norm_margin: float) -> str:
    if passed:
        return "nominal"
    if norm_margin <= -0.25:
        return "critical"
    return "review"


def highest_severity(results: list[RuleResult]) -> str:
    value = "nominal"
    for result in results:
        if SEVERITY_RANK[result.severity] > SEVERITY_RANK[value]:
            value = result.severity
    return value


def make_result(
    item: dict[str, Any],
    passed: bool,
    measured: dict[str, Any],
    reason: str,
    violation_time: float | None,
    recommendation: str | None,
    margin: float | None,
    limit: float | None,
) -> RuleResult:
    norm_margin = None if margin is None or limit is None else normalized_margin(margin, limit)
    severity = "review" if norm_margin is None else severity_for(passed, norm_margin)
    return RuleResult(
        rule_id=str(item["id"]),
        passed=passed,
        measured=measured,
        reason=reason,
        violation_time=violation_time,
        recommendation=None if passed else recommendation,
        safety_margin=margin,
        normalized_margin=norm_margin,
        severity=severity,
    )


def primary_failure(results: list[RuleResult]) -> RuleResult | None:
    failures = [result for result in results if not result.passed]
    if not failures:
        return None
    return min(
        failures,
        key=lambda result: (
            float("inf") if result.violation_time is None else result.violation_time,
            result.rule_id,
        ),
    )


def review(scenario: Scenario, rule_items: list[dict[str, Any]]) -> EvidenceCard:
    results: list[RuleResult] = []

    for item in rule_items:
        if not applies_to_family(item, scenario.family):
            continue

        kind = item.get("type")
        recommendation = recommendation_for(item)

        if kind == "radius_clearance":
            center_data = item["center"]
            center = Vec3(x=center_data["x"], y=center_data["y"], z=center_data["z"])
            limit = float(item["radius"])
            inside, event_time, value = path_inside_radius(scenario.planned_path, center, limit)
            closest = 0.0 if value is None else value
            margin = closest - limit
            results.append(
                make_result(
                    item=item,
                    passed=not inside,
                    measured={"closest_distance": value, "radius": limit},
                    reason=str(item.get("reason", "Radius clearance check.")),
                    violation_time=event_time if inside else None,
                    recommendation=recommendation,
                    margin=margin,
                    limit=limit,
                )
            )
            continue

        if kind == "tilt_limit":
            limit = float(item["max_deg"])
            value, event_time = max_tilt(scenario.planned_path)
            failed = value > limit
            margin = limit - value
            results.append(
                make_result(
                    item=item,
                    passed=not failed,
                    measured={"max_tilt_deg": value, "limit_deg": limit},
                    reason=str(item.get("reason", "Tilt limit check.")),
                    violation_time=event_time if failed else None,
                    recommendation=recommendation,
                    margin=margin,
                    limit=limit,
                )
            )
            continue

        if kind == "corridor_limit":
            limit = float(item["max_offset"])
            value, event_time = max_lateral_offset(scenario.planned_path)
            failed = value > limit
            margin = limit - value
            results.append(
                make_result(
                    item=item,
                    passed=not failed,
                    measured={"max_lateral_offset": value, "limit": limit},
                    reason=str(item.get("reason", "Corridor offset check.")),
                    violation_time=event_time if failed else None,
                    recommendation=recommendation,
                    margin=margin,
                    limit=limit,
                )
            )
            continue

        if kind == "speed_limit":
            limit = float(item["max_speed"])
            value, event_time = max_segment_speed(scenario.planned_path)
            failed = value > limit
            margin = limit - value
            results.append(
                make_result(
                    item=item,
                    passed=not failed,
                    measured={"max_segment_speed": value, "limit": limit},
                    reason=str(item.get("reason", "Segment speed check.")),
                    violation_time=event_time if failed else None,
                    recommendation=recommendation,
                    margin=margin,
                    limit=limit,
                )
            )
            continue

        results.append(
            RuleResult(
                rule_id=str(item.get("id", "unknown")),
                passed=False,
                measured={"kind": kind},
                reason="Unsupported check type.",
                recommendation="Review the unsupported check configuration before using this scenario.",
                severity="review",
            )
        )

    failure = primary_failure(results)
    failed_count = sum(1 for result in results if not result.passed)
    passed = failed_count == 0
    return EvidenceCard(
        scenario_id=scenario.id,
        scenario_family=scenario.family,
        decision=Decision.ALLOW if passed else Decision.REQUIRE_REVIEW,
        results=results,
        checked_count=len(results),
        failed_count=failed_count,
        primary_rule_id=None if failure is None else failure.rule_id,
        primary_violation_time=None if failure is None else failure.violation_time,
        primary_recommendation=None if failure is None else failure.recommendation,
        highest_severity=highest_severity(results),
        summary="All checks passed." if passed else "One or more checks require review.",
    )
