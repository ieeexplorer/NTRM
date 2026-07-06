from __future__ import annotations

import dataclasses

import pytest

from agent_control.bids import ActionKind, Bid, ControlAction


def test_bid_creation_and_fields() -> None:
    bid = Bid(
        agent_id="flex-1",
        kind="load_shed",
        bus=5,
        max_amount_mw=20.0,
        cost_per_mwh=1_000.0,
        duration_hours=0.25,
    )

    assert bid.agent_id == "flex-1"
    assert bid.kind == "load_shed"
    assert bid.bus == 5
    assert bid.max_amount_mw == 20.0
    assert bid.cost_per_mwh == 1_000.0
    assert bid.duration_hours == 0.25
    assert bid.generator_id is None


def test_bid_with_generator_id() -> None:
    bid = Bid(
        agent_id="gen-0",
        kind="generator_increase",
        bus=1,
        max_amount_mw=50.0,
        cost_per_mwh=100.0,
        duration_hours=0.25,
        generator_id=3,
    )

    assert bid.generator_id == 3
    assert bid.kind == "generator_increase"


def test_control_action_creation_and_fields() -> None:
    action = ControlAction(
        agent_id="flex-1",
        kind="load_shed",
        bus=5,
        amount_mw=10.0,
        cost_per_mwh=1_000.0,
        duration_hours=0.25,
    )

    assert action.agent_id == "flex-1"
    assert action.amount_mw == 10.0
    assert action.generator_id is None


def test_energy_mwh_property() -> None:
    action = ControlAction("a", "load_shed", 1, 10.0, 500.0, 0.5)

    assert action.energy_mwh == pytest.approx(5.0)  # 10 * 0.5


def test_cost_property() -> None:
    action = ControlAction("a", "load_shed", 1, 10.0, 500.0, 0.5)

    # energy = 5 MWh, cost = 5 * 500 = 2500
    assert action.cost == pytest.approx(2_500.0)


def test_bid_is_frozen() -> None:
    bid = Bid("a", "load_shed", 1, 10.0, 100.0, 0.25)

    with pytest.raises(dataclasses.FrozenInstanceError):
        bid.max_amount_mw = 20.0  # type: ignore[misc]


def test_control_action_is_frozen() -> None:
    action = ControlAction("a", "load_shed", 1, 10.0, 100.0, 0.25)

    with pytest.raises(dataclasses.FrozenInstanceError):
        action.amount_mw = 20.0  # type: ignore[misc]


def test_action_kind_literals() -> None:
    valid: ActionKind = "load_shed"
    assert valid in ("load_shed", "battery_injection", "generator_increase")
