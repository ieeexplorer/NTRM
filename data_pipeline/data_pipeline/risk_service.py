"""End-to-end assessment orchestration with explicit research boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from agent_control.controller import NetworkAwareController
from agent_control.environment import ControlPolicy, ScenarioOutcome, run_scenario
from cascade_ml.model import PowerCase

from .case_mapping import MappingConfig, MappingReport, map_snapshot_to_case
from .screening import RiskPredictor, ScreeningResult, screen_contingencies
from .snapshot import OperatingSnapshot


@dataclass(frozen=True)
class AssessmentReport:
    snapshot: OperatingSnapshot
    mapping: MappingReport
    screening: tuple[ScreeningResult, ...]
    simulated_intervention: ScenarioOutcome | None


def assess_snapshot(
    snapshot: OperatingSnapshot,
    base_case: PowerCase,
    contingencies: list[tuple[int, ...]],
    *,
    predictor: RiskPredictor | None = None,
    mapping_config: MappingConfig | None = None,
    resource_config=None,
    include_control: bool = True,
    control_risk_threshold: float = 0.5,
    severe_threshold_fraction: float = 0.2,
) -> AssessmentReport:
    mapping = map_snapshot_to_case(snapshot, base_case, mapping_config)
    screening = screen_contingencies(
        mapping.case,
        contingencies,
        predictor=predictor,
        severe_threshold_fraction=severe_threshold_fraction,
    )
    intervention = None
    trigger_index = None
    if include_control and predictor is not None:
        for idx, sr in enumerate(screening):
            if (
                sr.conditional_probability is not None
                and sr.conditional_probability >= control_risk_threshold
            ):
                trigger_index = idx
                break
    if trigger_index is not None:
        intervention = run_scenario(
            mapping.case,
            screening[trigger_index].outage_branch_ids,
            demonstration_agents(mapping.case, resource_config=resource_config),
            policy=ControlPolicy.AUCTION,
            controller=NetworkAwareController(),
        )
    return AssessmentReport(snapshot, mapping, tuple(screening), intervention)


def demonstration_agents(case: PowerCase, resource_config=None):
    """Create documented synthetic resources; these are not real GB assets."""
    from agent_control.sensitivity import PortfolioConfig, build_portfolio

    return build_portfolio(case, PortfolioConfig(name="demonstration"), resource_config=resource_config)
