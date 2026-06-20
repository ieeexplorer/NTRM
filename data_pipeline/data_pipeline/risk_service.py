"""End-to-end assessment orchestration with explicit research boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from agent_control.controller import NetworkAwareController
from agent_control.environment import ControlPolicy, ScenarioOutcome, run_scenario
from agent_control.resources import BatteryAgent, FlexibleLoadAgent, GeneratorAgent
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
    include_control: bool = True,
) -> AssessmentReport:
    mapping = map_snapshot_to_case(snapshot, base_case, mapping_config)
    screening = screen_contingencies(mapping.case, contingencies, predictor=predictor)
    intervention = None
    if include_control and screening:
        intervention = run_scenario(
            mapping.case,
            screening[0].outage_branch_ids,
            demonstration_agents(mapping.case),
            policy=ControlPolicy.AUCTION,
            controller=NetworkAwareController(),
        )
    return AssessmentReport(snapshot, mapping, tuple(screening), intervention)


def demonstration_agents(case: PowerCase):
    """Create documented synthetic resources; these are not real GB assets."""

    load_buses = sorted(case.loads_mw, key=case.loads_mw.get, reverse=True)
    agents = []
    for bus in load_buses[:3]:
        load = case.loads_mw[bus]
        agents.append(
            FlexibleLoadAgent(
                f"synthetic-flex-{bus}",
                bus,
                max_shed_mw=min(50.0, 0.1 * load),
                minimum_served_mw=0.8 * load,
            )
        )
    for bus in load_buses[3:5]:
        agents.append(
            BatteryAgent(
                f"synthetic-battery-{bus}",
                bus,
                max_power_mw=50.0,
                energy_capacity_mwh=25.0,
                state_of_charge=0.8,
            )
        )
    for generator in case.generators:
        if generator.max_mw > generator.scheduled_mw:
            agents.append(
                GeneratorAgent(
                    f"synthetic-generator-{generator.generator_id}",
                    generator.generator_id,
                    max_increase_mw=50.0,
                    ramp_mw_per_minute=10.0,
                    response_minutes=5.0,
                )
            )
    return agents
