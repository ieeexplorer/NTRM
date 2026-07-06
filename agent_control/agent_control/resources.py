"""Resource agents with explicit power, energy, ramp, and cost constraints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .bids import Bid
from .state import OperatingState


class ResourceAgent(Protocol):
    @property
    def agent_id(self) -> str: ...

    def propose(self, state: OperatingState, duration_hours: float) -> Bid | None: ...


@dataclass(frozen=True)
class FlexibleLoadAgent:
    agent_id: str
    bus: int
    max_shed_mw: float
    minimum_served_mw: float = 0.0
    cost_per_mwh: float = 1_000.0

    def propose(self, state: OperatingState, duration_hours: float) -> Bid | None:
        available = min(
            self.max_shed_mw,
            max(state.remaining_physical_load_mw(self.bus) - self.minimum_served_mw, 0.0),
        )
        if available <= 0:
            return None
        return Bid(
            self.agent_id,
            "load_shed",
            self.bus,
            available,
            self.cost_per_mwh,
            duration_hours,
        )


@dataclass(frozen=True)
class BatteryAgent:
    agent_id: str
    bus: int
    max_power_mw: float
    energy_capacity_mwh: float
    state_of_charge: float = 1.0
    discharge_efficiency: float = 0.95
    cost_per_mwh: float = 50.0

    def propose(self, state: OperatingState, duration_hours: float) -> Bid | None:
        if duration_hours <= 0:
            raise ValueError("duration_hours must be positive")
        if not 0 <= self.state_of_charge <= 1:
            raise ValueError("state_of_charge must be between 0 and 1")
        energy_limited_power = (
            self.energy_capacity_mwh
            * self.state_of_charge
            * self.discharge_efficiency
            / duration_hours
        )
        available = min(
            self.max_power_mw,
            energy_limited_power,
            state.remaining_net_load_mw(self.bus),
        )
        if available <= 0:
            return None
        return Bid(
            self.agent_id,
            "battery_injection",
            self.bus,
            available,
            self.cost_per_mwh,
            duration_hours,
        )


@dataclass(frozen=True)
class GeneratorAgent:
    agent_id: str
    generator_id: int
    max_increase_mw: float
    ramp_mw_per_minute: float
    response_minutes: float
    cost_per_mwh: float = 100.0

    def propose(self, state: OperatingState, duration_hours: float) -> Bid | None:
        generators = {generator.generator_id: generator for generator in state.base_case.generators}
        if self.generator_id not in generators:
            raise ValueError(f"Unknown generator ID: {self.generator_id}")
        generator = generators[self.generator_id]
        already_selected = state.generator_increase_mw.get(self.generator_id, 0.0)
        headroom = max(generator.max_mw - generator.scheduled_mw - already_selected, 0.0)
        available = min(
            self.max_increase_mw,
            self.ramp_mw_per_minute * self.response_minutes,
            headroom,
        )
        if available <= 0:
            return None
        return Bid(
            self.agent_id,
            "generator_increase",
            generator.bus,
            available,
            self.cost_per_mwh,
            duration_hours,
            generator_id=self.generator_id,
        )
