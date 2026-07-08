"""Edge-case tests for the NetworkAwareController."""

from __future__ import annotations

import pytest

from agent_control.controller import NetworkAwareController, _overload_excess
from agent_control.resources import FlexibleLoadAgent
from agent_control.state import OperatingState


def test_budget_limits_actions(overloaded_case):
    """Controller stops when cumulative cost reaches the budget."""
    # overloaded_case has 100 MW load on bus 3, branches rated at 80 MVA.
    # Loading ratio is 100/80 = 1.25, target 0.9, so excess ≈ 0.35.
    # Each 10 MW shed costs 10 * 0.25 * 1000 = 2500.
    # A budget of 5000 allows at most 1 full step (cost 2500); the second
    # would push cost to 5000 which equals budget so it is skipped.
    controller = NetworkAwareController(
        target_loading_ratio=0.9,
        action_step_mw=10.0,
        budget=5000.0,
    )
    agents = [FlexibleLoadAgent("flex-3", 3, max_shed_mw=40.0, cost_per_mwh=1_000.0)]
    state = OperatingState(overloaded_case)

    result = controller.control(state, (), agents, selection_mode="auction")

    # With a very tight budget the controller should either not meet target
    # or have very few actions.
    assert len(result.state.actions) <= 2
    # Verify cost never exceeds budget
    assert result.state.intervention_cost <= 5000.0 + 1e-9


def test_maximum_actions_stops_controller(overloaded_case):
    """Controller stops after maximum_actions even if target not met."""
    # Use a very small action step so the controller cannot resolve the
    # overload within 2 actions.  Loading ratio starts at 1.25, target 0.9.
    # Each step sheds 1 MW → very slow progress.
    controller = NetworkAwareController(
        target_loading_ratio=0.9,
        action_step_mw=1.0,
        maximum_actions=2,
    )
    agents = [FlexibleLoadAgent("flex-3", 3, max_shed_mw=40.0)]
    state = OperatingState(overloaded_case)

    result = controller.control(state, (), agents, selection_mode="auction")

    # With only 2 steps of 1 MW each the overload is far from resolved.
    assert len(result.state.actions) == 2
    assert not result.target_met


def test_empty_agents_returns_no_change(overloaded_case):
    """Controller with no agents returns before/after as equal."""
    controller = NetworkAwareController(target_loading_ratio=0.9)
    state = OperatingState(overloaded_case)

    result = controller.control(state, (), (), selection_mode="auction")

    assert result.before.loading_ratios == result.after.loading_ratios
    assert result.state.preventive_load_shed_mw == 0.0
    assert len(result.state.actions) == 0
    assert not result.target_met


def test_zero_budget_returns_no_change(overloaded_case):
    """Controller with budget=0 cannot take any action."""
    controller = NetworkAwareController(
        target_loading_ratio=0.9,
        budget=0.0,
    )
    agents = [FlexibleLoadAgent("flex-3", 3, max_shed_mw=40.0, cost_per_mwh=1_000.0)]
    state = OperatingState(overloaded_case)

    result = controller.control(state, (), agents, selection_mode="auction")

    # No action should be taken because even a single step exceeds budget.
    assert result.before.loading_ratios == result.after.loading_ratios
    assert len(result.state.actions) == 0
    assert not result.target_met


def test_overload_excess_zero_when_all_under_target(overloaded_case):
    """_overload_excess returns 0 when no branch exceeds the target."""
    # Create a power flow result with loading ratios all below target.
    from cascade_ml.power_flow import PowerFlowResult

    pf = PowerFlowResult(
        flows_mw={0: 50.0, 1: 50.0},
        loading_ratios={0: 0.5, 1: 0.6},
        angles_rad={1: 0.0, 2: -0.05, 3: -0.10},
        unserved_mw=0.0,
        served_load_mw=100.0,
        island_count=1,
    )
    assert _overload_excess(pf, 0.9) == pytest.approx(0.0)


def test_overload_excess_sums_only_excess(overloaded_case):
    """_overload_excess only counts the part above the target."""
    from cascade_ml.power_flow import PowerFlowResult

    pf = PowerFlowResult(
        flows_mw={0: 50.0, 1: 50.0},
        loading_ratios={0: 0.5, 1: 1.2},
        angles_rad={1: 0.0, 2: -0.05, 3: -0.10},
        unserved_mw=0.0,
        served_load_mw=100.0,
        island_count=1,
    )
    # Only branch 1 exceeds 0.9; excess = 1.2 - 0.9 = 0.3
    assert _overload_excess(pf, 0.9) == pytest.approx(0.3)


def test_invalid_selection_mode_raises(overloaded_case):
    """An unknown selection_mode raises ValueError."""
    controller = NetworkAwareController(target_loading_ratio=0.9)
    state = OperatingState(overloaded_case)

    with pytest.raises(ValueError, match="Unknown selection mode"):
        controller.control(state, (), (), selection_mode="invalid")  # type: ignore[arg-type]
