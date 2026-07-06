from __future__ import annotations

from typing import Any

from src.oracle_omega.core.models import Decision, EvidenceCard, RuleResult, Scenario, Vec3
from src.oracle_omega.spatial.checks import max_tilt, path_inside_radius


def review(scenario: Scenario, rule_items: list[dict[str, Any]]) -> EvidenceCard:
    results: list[RuleResult] = []

    for item in rule_items:
        kind = item.get("type")

        if kind == "radius_clearance":
            center_data = item["center"]
            center = Vec3(x=center_data["x"], y=center_data["y"], z=center_data["z"])
            limit = float(item["radius"])
            inside, event_time, value = path_inside_radius(scenario.planned_path, center, limit)
            results.append(
                RuleResult(
                    rule_id=str(item["id"]),
                    passed=not inside,
                    measured={"closest_distance": value, "radius": limit},
                    reason=str(item.get("reason", "Radius clearance check.")),
                    violation_time=event_time if inside else None,
                )
            )
            continue

        if kind == "tilt_limit":
            limit = float(item["max_deg"])
            value, event_time = max_tilt(scenario.planned_path)
            failed = value > limit
            results.append(
                RuleResult(
                    rule_id=str(item["id"]),
                    passed=not failed,
                    measured={"max_tilt_deg": value, "limit_deg": limit},
                    reason=str(item.get("reason", "Tilt limit check.")),
                    violation_time=event_time if failed else None,
                )
            )
            continue

        results.append(
            RuleResult(
                rule_id=str(item.get("id", "unknown")),
                passed=False,
                measured={"kind": kind},
                reason="Unsupported check type.",
            )
        )

    passed = all(result.passed for result in results)
    return EvidenceCard(
        scenario_id=scenario.id,
        decision=Decision.ALLOW if passed else Decision.REQUIRE_REVIEW,
        results=results,
        summary="All checks passed." if passed else "One or more checks require review.",
    )
