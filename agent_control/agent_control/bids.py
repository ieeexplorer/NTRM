"""Typed resource bids and selected control actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ActionKind = Literal["load_shed", "battery_injection", "generator_increase"]


@dataclass(frozen=True)
class Bid:
    agent_id: str
    kind: ActionKind
    bus: int
    max_amount_mw: float
    cost_per_mwh: float
    duration_hours: float
    generator_id: int | None = None


@dataclass(frozen=True)
class ControlAction:
    agent_id: str
    kind: ActionKind
    bus: int
    amount_mw: float
    cost_per_mwh: float
    duration_hours: float
    generator_id: int | None = None

    @property
    def energy_mwh(self) -> float:
        return self.amount_mw * self.duration_hours

    @property
    def cost(self) -> float:
        return self.energy_mwh * self.cost_per_mwh
