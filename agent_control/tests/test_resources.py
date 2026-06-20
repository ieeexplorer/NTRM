from __future__ import annotations

import pytest

from agent_control.resources import BatteryAgent, FlexibleLoadAgent, GeneratorAgent
from agent_control.state import OperatingState


def test_battery_bid_respects_energy_power_and_local_net_load(overloaded_case) -> None:
    state = OperatingState(overloaded_case)
    battery = BatteryAgent(
        "battery-3",
        bus=3,
        max_power_mw=20.0,
        energy_capacity_mwh=10.0,
        state_of_charge=0.5,
        discharge_efficiency=0.9,
    )

    bid = battery.propose(state, duration_hours=0.25)

    assert bid is not None
    assert bid.max_amount_mw == pytest.approx(18.0)


def test_flexible_load_respects_minimum_service(overloaded_case) -> None:
    bid = FlexibleLoadAgent("flex-3", 3, max_shed_mw=50.0, minimum_served_mw=80.0).propose(
        OperatingState(overloaded_case), 0.25
    )
    assert bid is not None
    assert bid.max_amount_mw == pytest.approx(20.0)


def test_generator_bid_respects_ramp_and_headroom(overloaded_case) -> None:
    bid = GeneratorAgent(
        "gen-0",
        generator_id=0,
        max_increase_mw=50.0,
        ramp_mw_per_minute=2.0,
        response_minutes=5.0,
    ).propose(OperatingState(overloaded_case), 0.25)
    assert bid is None  # This generator is already at its maximum.
