from __future__ import annotations

from pydantic import BaseModel

from src.oracle_omega.buffered_repair import build_buffered_repair_candidate
from src.oracle_omega.core.models import ReplayBundle, RobustnessReport, Scenario
from src.oracle_omega.replay import build_replay_bundle
from src.oracle_omega.reviewer import review
from src.oracle_omega.robustness import build_robustness_report


class RobustnessVisualizationBundle(BaseModel):
    scenario_id: str
    scenario_family: str
    robustness_report: RobustnessReport
    nominal_replay: ReplayBundle
    stress_replay: ReplayBundle | None = None
    buffered_repair_replay: ReplayBundle | None = None


def build_robustness_visualization_bundle(
    scenario: Scenario,
    rule_items: list[dict],
    sample_override: int | None = None,
    compare_repair: bool = False,
) -> RobustnessVisualizationBundle:
    nominal_evidence = review(scenario, rule_items)
    report = build_robustness_report(
        scenario,
        rule_items,
        sample_override=sample_override,
        compare_repair=compare_repair,
    )
    nominal_replay = build_replay_bundle(scenario, nominal_evidence)

    stress_replay = None
    stress_case = report.adversarial_case
    if stress_case.found and stress_case.scenario is not None and stress_case.evidence is not None:
        stress_replay = build_replay_bundle(stress_case.scenario, stress_case.evidence)

    buffered_repair_replay = None
    if compare_repair and report.repair_comparison is not None:
        sigma_buffer = report.repair_comparison.selected_sigma_buffer or 3.0
        repair = build_buffered_repair_candidate(
            scenario,
            rule_items,
            nominal_evidence,
            sigma_buffer=sigma_buffer,
        )
        if repair.available and repair.repaired_scenario is not None and repair.repaired_evidence is not None:
            buffered_repair_replay = build_replay_bundle(repair.repaired_scenario, repair.repaired_evidence)

    return RobustnessVisualizationBundle(
        scenario_id=scenario.id,
        scenario_family=scenario.family,
        robustness_report=report,
        nominal_replay=nominal_replay,
        stress_replay=stress_replay,
        buffered_repair_replay=buffered_repair_replay,
    )
