from __future__ import annotations

import random
from collections import Counter
from enum import Enum
from typing import Any

from src.oracle_omega.core.models import (
    AdversarialCase,
    Decision,
    EvidenceCard,
    MonteCarloSummary,
    PathSample,
    RobustnessReport,
    Scenario,
    UncertaintyConfig,
    Vec3,
)
from src.oracle_omega.reviewer import review

SEVERITY_RANK = {"nominal": 0, "review": 1, "critical": 2}
STRESS_DIRECTIONS = (
    {"x": 0.0, "y": 1.0, "z": 0.0},
    {"x": 0.0, "y": -1.0, "z": 0.0},
    {"x": 0.0, "y": 0.0, "z": 1.0},
    {"x": 0.0, "y": 0.0, "z": -1.0},
    {"x": 0.0, "y": 0.7071, "z": 0.7071},
    {"x": 0.0, "y": -0.7071, "z": 0.7071},
)


def enum_key(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def vec3_from_mapping(value: Any, default: Vec3) -> Vec3:
    if not isinstance(value, dict):
        return default
    return Vec3(
        x=float(value.get("x", default.x)),
        y=float(value.get("y", default.y)),
        z=float(value.get("z", default.z)),
    )


def uncertainty_from_scenario(
    scenario: Scenario,
    sample_override: int | None = None,
    seed_override: int | None = None,
) -> UncertaintyConfig:
    raw = scenario.parameters.get("uncertainty", {})
    if not isinstance(raw, dict):
        raw = {}

    config = UncertaintyConfig(
        position_sigma=vec3_from_mapping(raw.get("position_sigma", {}), Vec3(x=0.0, y=0.15, z=0.05)),
        timing_sigma=float(raw.get("timing_sigma", 0.1)),
        attitude_sigma_deg=vec3_from_mapping(raw.get("attitude_sigma_deg", {}), Vec3(x=0.5, y=0.5, z=0.25)),
        samples=int(raw.get("samples", 100)),
        seed=int(raw.get("seed", 7)),
    )
    if sample_override is not None:
        config.samples = sample_override
    if seed_override is not None:
        config.seed = seed_override
    return config


def copy_sample_with_noise(sample: PathSample, rng: random.Random, config: UncertaintyConfig) -> PathSample:
    return PathSample(
        t=sample.t,
        position=Vec3(
            x=sample.position.x + rng.gauss(0.0, config.position_sigma.x),
            y=sample.position.y + rng.gauss(0.0, config.position_sigma.y),
            z=sample.position.z + rng.gauss(0.0, config.position_sigma.z),
        ),
        attitude_deg=Vec3(
            x=sample.attitude_deg.x + rng.gauss(0.0, config.attitude_sigma_deg.x),
            y=sample.attitude_deg.y + rng.gauss(0.0, config.attitude_sigma_deg.y),
            z=sample.attitude_deg.z + rng.gauss(0.0, config.attitude_sigma_deg.z),
        ),
    )


def perturb_scenario(scenario: Scenario, config: UncertaintyConfig, rng: random.Random, index: int) -> Scenario:
    path = [copy_sample_with_noise(sample, rng, config) for sample in scenario.planned_path]
    if path:
        path[0].t = scenario.planned_path[0].t
    for previous_original, current_original, previous_new, current_new in zip(
        scenario.planned_path,
        scenario.planned_path[1:],
        path,
        path[1:],
    ):
        original_dt = max(current_original.t - previous_original.t, 0.001)
        perturbed_dt = max(0.001, original_dt + rng.gauss(0.0, config.timing_sigma))
        current_new.t = previous_new.t + perturbed_dt

    return Scenario(
        id=f"{scenario.id}-uncertainty-{index:04d}",
        name=f"{scenario.name} Uncertainty Sample {index}",
        family=scenario.family,
        planned_path=path,
        parameters={**scenario.parameters, "uncertainty_sample_index": index},
    )


def failed_rule_ids(evidence: EvidenceCard) -> list[str]:
    return [result.rule_id for result in evidence.results if not result.passed]


def highest_severity(values: list[str]) -> str:
    result = "nominal"
    for value in values:
        if SEVERITY_RANK.get(value, 0) > SEVERITY_RANK[result]:
            result = value
    return result


def run_monte_carlo(
    scenario: Scenario,
    rule_items: list[dict],
    config: UncertaintyConfig,
) -> MonteCarloSummary:
    rng = random.Random(config.seed)
    decision_counts: Counter[str] = Counter()
    failure_rule_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()
    severities: list[str] = []
    pass_count = 0
    fail_count = 0

    for index in range(config.samples):
        sample = perturb_scenario(scenario, config, rng, index)
        evidence = review(sample, rule_items)
        decision_counts[enum_key(evidence.decision)] += 1
        severity_counts[evidence.highest_severity] += 1
        severities.append(evidence.highest_severity)
        if evidence.decision == Decision.ALLOW:
            pass_count += 1
        else:
            fail_count += 1
            for rule_id in failed_rule_ids(evidence):
                failure_rule_counts[rule_id] += 1

    most_common_failure = failure_rule_counts.most_common(1)[0][0] if failure_rule_counts else None
    return MonteCarloSummary(
        sample_count=config.samples,
        pass_count=pass_count,
        fail_count=fail_count,
        failure_probability=fail_count / config.samples if config.samples else 0.0,
        decision_counts=counter_to_dict(decision_counts),
        failure_rule_counts=counter_to_dict(failure_rule_counts),
        severity_counts=counter_to_dict(severity_counts),
        most_common_failure=most_common_failure,
        worst_case_severity=highest_severity(severities),
    )


def directed_stress_case(scenario: Scenario, direction: dict[str, float], magnitude: float) -> Scenario:
    path = []
    for sample in scenario.planned_path:
        path.append(
            PathSample(
                t=sample.t,
                position=Vec3(
                    x=sample.position.x + direction.get("x", 0.0) * magnitude,
                    y=sample.position.y + direction.get("y", 0.0) * magnitude,
                    z=sample.position.z + direction.get("z", 0.0) * magnitude,
                ),
                attitude_deg=Vec3(
                    x=sample.attitude_deg.x,
                    y=sample.attitude_deg.y,
                    z=sample.attitude_deg.z,
                ),
            )
        )

    return Scenario(
        id=f"{scenario.id}-stress-search",
        name=f"{scenario.name} Stress Candidate",
        family=scenario.family,
        planned_path=path,
        parameters={**scenario.parameters, "stress_direction": direction, "stress_magnitude": magnitude},
    )


def find_worst_case_stress(
    scenario: Scenario,
    rule_items: list[dict],
    max_magnitude: float = 2.0,
    steps: int = 40,
) -> AdversarialCase:
    best_scenario = None
    best_evidence = None
    best_direction = None
    best_magnitude = None

    for direction in STRESS_DIRECTIONS:
        for step in range(1, steps + 1):
            magnitude = max_magnitude * step / steps
            candidate = directed_stress_case(scenario, direction, magnitude)
            evidence = review(candidate, rule_items)
            if evidence.decision == Decision.ALLOW:
                continue
            if best_magnitude is None or magnitude < best_magnitude:
                best_scenario = candidate
                best_evidence = evidence
                best_direction = direction
                best_magnitude = magnitude
            break

    if best_scenario is None or best_evidence is None or best_direction is None or best_magnitude is None:
        return AdversarialCase(found=False, description="No failing stress perturbation found within the configured search radius.")

    return AdversarialCase(
        found=True,
        triggered_rule=best_evidence.primary_rule_id,
        perturbation_norm=best_magnitude,
        violation_time=best_evidence.primary_violation_time,
        direction=best_direction,
        scenario=best_scenario,
        evidence=best_evidence,
        description=(
            f"Small directed stress perturbation of magnitude {best_magnitude:.3f} triggered "
            f"{best_evidence.primary_rule_id} at T+{best_evidence.primary_violation_time}."
        ),
    )


def build_robustness_report(
    scenario: Scenario,
    rule_items: list[dict],
    sample_override: int | None = None,
    seed_override: int | None = None,
) -> RobustnessReport:
    config = uncertainty_from_scenario(scenario, sample_override, seed_override)
    nominal = review(scenario, rule_items)
    monte_carlo = run_monte_carlo(scenario, rule_items, config)
    stress_case = find_worst_case_stress(scenario, rule_items)

    return RobustnessReport(
        scenario_id=scenario.id,
        scenario_family=scenario.family,
        nominal_decision=nominal.decision,
        nominal_failed_count=nominal.failed_count,
        nominal_highest_severity=nominal.highest_severity,
        uncertainty=config,
        monte_carlo=monte_carlo,
        adversarial_case=stress_case,
    )
