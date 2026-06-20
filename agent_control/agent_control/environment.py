"""Paired uncontrolled and controlled cascade experiments."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from cascade_ml.cascade import simulate_cascade
from cascade_ml.model import PowerCase

from .controller import NetworkAwareController
from .predictor import RiskPredictor
from .resources import ResourceAgent
from .state import OperatingState


class ControlPolicy(str, Enum):
    NO_CONTROL = "no_control"
    CENTRALISED = "centralised"
    AUCTION = "auction"
    RISK_GATED_AUCTION = "risk_gated_auction"


@dataclass(frozen=True)
class ScenarioOutcome:
    policy: ControlPolicy
    contingency_key: str
    risk_probability: float | None
    activated: bool
    target_met: bool | None
    baseline_unserved_mw: float
    controlled_unserved_mw: float
    preventive_load_shed_mw: float
    battery_injection_mw: float
    generator_increase_mw: float
    intervention_cost: float
    action_count: int
    baseline_cascade_generations: int
    controlled_cascade_generations: int

    @property
    def gross_avoided_blackout_mw(self) -> float:
        return self.baseline_unserved_mw - self.controlled_unserved_mw

    @property
    def net_avoided_loss_mw(self) -> float:
        return self.baseline_unserved_mw - (
            self.controlled_unserved_mw + self.preventive_load_shed_mw
        )


def run_scenario(
    case: PowerCase,
    initial_outages: tuple[int, ...],
    agents: Sequence[ResourceAgent],
    *,
    policy: ControlPolicy,
    controller: NetworkAwareController | None = None,
    predictor: RiskPredictor | None = None,
    risk_threshold: float = 0.5,
) -> ScenarioOutcome:
    baseline = simulate_cascade(case, initial_outages)
    state = OperatingState(case)
    risk: float | None = None
    activated = policy not in (ControlPolicy.NO_CONTROL, ControlPolicy.RISK_GATED_AUCTION)
    if policy == ControlPolicy.RISK_GATED_AUCTION:
        if predictor is None:
            raise ValueError("Risk-gated policy requires a predictor")
        risk = predictor.predict_probability(case, initial_outages)
        activated = risk >= risk_threshold

    target_met: bool | None = None
    if activated:
        controller = controller or NetworkAwareController()
        mode = "centralised" if policy == ControlPolicy.CENTRALISED else "auction"
        control = controller.control(state, initial_outages, agents, selection_mode=mode)
        state = control.state
        target_met = control.target_met
    controlled = simulate_cascade(state.to_power_case(), initial_outages)

    return ScenarioOutcome(
        policy=policy,
        contingency_key="|".join(map(str, initial_outages)),
        risk_probability=risk,
        activated=activated,
        target_met=target_met,
        baseline_unserved_mw=baseline.unserved_mw,
        controlled_unserved_mw=controlled.unserved_mw,
        preventive_load_shed_mw=state.preventive_load_shed_mw,
        battery_injection_mw=state.battery_injection_total_mw,
        generator_increase_mw=state.generator_increase_total_mw,
        intervention_cost=state.intervention_cost,
        action_count=len(state.actions),
        baseline_cascade_generations=len(baseline.steps),
        controlled_cascade_generations=len(controlled.steps),
    )
