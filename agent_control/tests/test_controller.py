from __future__ import annotations

import pytest

from agent_control.controller import NetworkAwareController
from agent_control.resources import FlexibleLoadAgent
from agent_control.state import OperatingState


@pytest.mark.parametrize("mode", ["centralised", "auction"])
def test_controller_measures_action_effect_and_resolves_overload(overloaded_case, mode) -> None:
    controller = NetworkAwareController(target_loading_ratio=0.9, action_step_mw=10.0)
    agents = [FlexibleLoadAgent("flex-3", 3, max_shed_mw=40.0)]

    result = controller.control(OperatingState(overloaded_case), (), agents, selection_mode=mode)

    assert result.target_met
    assert result.before.loading_ratios[0] == pytest.approx(1.25)
    assert result.after.loading_ratios[0] == pytest.approx(0.875)
    assert result.state.preventive_load_shed_mw == pytest.approx(30.0)
    assert len(result.state.actions) == 3
