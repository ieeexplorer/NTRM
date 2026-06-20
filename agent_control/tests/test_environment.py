from __future__ import annotations

import pytest

from agent_control.controller import NetworkAwareController
from agent_control.environment import ControlPolicy, run_scenario
from agent_control.resources import FlexibleLoadAgent


class FixedRiskPredictor:
    def __init__(self, probability: float) -> None:
        self.probability = probability

    def predict_probability(self, case, initial_outages) -> float:
        return self.probability


def test_control_separates_preventive_shed_from_blackout_loss(overloaded_case) -> None:
    outcome = run_scenario(
        overloaded_case,
        (),
        [FlexibleLoadAgent("flex-3", 3, max_shed_mw=40.0)],
        policy=ControlPolicy.AUCTION,
        controller=NetworkAwareController(target_loading_ratio=0.9, action_step_mw=10.0),
    )

    assert outcome.baseline_unserved_mw == pytest.approx(100.0)
    assert outcome.controlled_unserved_mw == pytest.approx(0.0)
    assert outcome.preventive_load_shed_mw == pytest.approx(30.0)
    assert outcome.gross_avoided_blackout_mw == pytest.approx(100.0)
    assert outcome.net_avoided_loss_mw == pytest.approx(70.0)


def test_risk_gate_does_not_activate_below_threshold(overloaded_case) -> None:
    outcome = run_scenario(
        overloaded_case,
        (),
        [FlexibleLoadAgent("flex-3", 3, max_shed_mw=40.0)],
        policy=ControlPolicy.RISK_GATED_AUCTION,
        predictor=FixedRiskPredictor(0.2),
        risk_threshold=0.5,
    )

    assert not outcome.activated
    assert outcome.action_count == 0
    assert outcome.controlled_unserved_mw == outcome.baseline_unserved_mw
