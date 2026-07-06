from __future__ import annotations

import pytest

from agent_control.bids import ControlAction
from agent_control.state import OperatingState
from cascade_ml.model import Branch, Generator, PowerCase


@pytest.fixture
def three_bus_case() -> PowerCase:
    return PowerCase(
        name="three_bus",
        base_mva=100.0,
        buses=(1, 2, 3),
        loads_mw={1: 0.0, 2: 50.0, 3: 50.0},
        generators=(Generator(0, 1, 80.0, 100.0),),
        branches=(
            Branch(0, 1, 2, 0.1, 200.0),
            Branch(1, 2, 3, 0.1, 200.0),
        ),
    )


@pytest.fixture
def initial_state(three_bus_case) -> OperatingState:
    return OperatingState(three_bus_case)


def test_operating_state_creation(initial_state) -> None:
    assert initial_state.load_shed_mw == {}
    assert initial_state.battery_injection_mw == {}
    assert initial_state.generator_increase_mw == {}
    assert initial_state.actions == ()


def test_apply_with_load_shed_action(initial_state) -> None:
    action = ControlAction("agent-1", "load_shed", 2, 10.0, 1000.0, 0.25)
    new_state = initial_state.apply(action)

    assert new_state.load_shed_mw[2] == 10.0
    assert len(new_state.actions) == 1
    assert new_state.actions[0] is action


def test_apply_with_battery_injection_action(initial_state) -> None:
    action = ControlAction("agent-2", "battery_injection", 3, 5.0, 50.0, 0.25)
    new_state = initial_state.apply(action)

    assert new_state.battery_injection_mw[3] == 5.0
    assert len(new_state.actions) == 1


def test_apply_with_generator_increase_action(initial_state) -> None:
    action = ControlAction("agent-3", "generator_increase", 1, 10.0, 100.0, 0.25, generator_id=0)
    new_state = initial_state.apply(action)

    assert new_state.generator_increase_mw[0] == 10.0
    assert len(new_state.actions) == 1


def test_apply_raises_for_negative_amount(initial_state) -> None:
    action = ControlAction("agent-1", "load_shed", 2, -1.0, 1000.0, 0.25)

    with pytest.raises(ValueError, match="positive"):
        initial_state.apply(action)


def test_apply_raises_for_generator_action_without_generator_id(initial_state) -> None:
    action = ControlAction("agent-3", "generator_increase", 1, 10.0, 100.0, 0.25)

    with pytest.raises(ValueError, match="generator_id"):
        initial_state.apply(action)


def test_to_power_case_correctly_modifies_loads_and_generators(initial_state) -> None:
    shed_action = ControlAction("a1", "load_shed", 2, 10.0, 1000.0, 0.25)
    battery_action = ControlAction("a2", "battery_injection", 3, 5.0, 50.0, 0.25)
    gen_action = ControlAction("a3", "generator_increase", 1, 10.0, 100.0, 0.25, generator_id=0)

    state = initial_state.apply(shed_action).apply(battery_action).apply(gen_action)
    modified = state.to_power_case()

    # Bus 2: 50 - 10 (shed) = 40
    assert modified.loads_mw[2] == pytest.approx(40.0)
    # Bus 3: 50 - 5 (battery) = 45
    assert modified.loads_mw[3] == pytest.approx(45.0)
    # Generator 0: 80 + 10 (increase), capped at 100
    assert modified.generators[0].scheduled_mw == pytest.approx(90.0)


def test_to_power_case_generator_capped_at_max(initial_state) -> None:
    action = ControlAction("a1", "generator_increase", 1, 30.0, 100.0, 0.25, generator_id=0)
    state = initial_state.apply(action)
    modified = state.to_power_case()

    # Generator 0: min(80 + 30, 100) = 100
    assert modified.generators[0].scheduled_mw == pytest.approx(100.0)


def test_remaining_physical_load_mw(initial_state) -> None:
    action = ControlAction("a1", "load_shed", 2, 10.0, 1000.0, 0.25)
    state = initial_state.apply(action)

    assert state.remaining_physical_load_mw(2) == pytest.approx(40.0)
    assert state.remaining_physical_load_mw(3) == pytest.approx(50.0)


def test_remaining_physical_load_mw_clamps_at_zero(initial_state) -> None:
    action = ControlAction("a1", "load_shed", 2, 60.0, 1000.0, 0.25)
    state = initial_state.apply(action)

    assert state.remaining_physical_load_mw(2) == pytest.approx(0.0)


def test_remaining_net_load_mw(initial_state) -> None:
    shed = ControlAction("a1", "load_shed", 3, 10.0, 1000.0, 0.25)
    battery = ControlAction("a2", "battery_injection", 3, 15.0, 50.0, 0.25)
    state = initial_state.apply(shed).apply(battery)

    # remaining physical = 50 - 10 = 40; net = 40 - 15 = 25
    assert state.remaining_net_load_mw(3) == pytest.approx(25.0)


def test_preventive_load_shed_mw_property(initial_state) -> None:
    action1 = ControlAction("a1", "load_shed", 2, 10.0, 1000.0, 0.25)
    action2 = ControlAction("a2", "load_shed", 3, 15.0, 1000.0, 0.25)
    state = initial_state.apply(action1).apply(action2)

    assert state.preventive_load_shed_mw == pytest.approx(25.0)


def test_intervention_cost_property(initial_state) -> None:
    # energy = amount * duration; cost = energy * cost_per_mwh
    action = ControlAction("a1", "load_shed", 2, 10.0, 100.0, 0.25)
    state = initial_state.apply(action)

    # energy = 10 * 0.25 = 2.5 MWh; cost = 2.5 * 100 = 250
    assert state.intervention_cost == pytest.approx(250.0)
