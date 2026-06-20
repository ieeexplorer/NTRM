"""Immutable controllable operating state layered over a static power case."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from cascade_ml.model import PowerCase

from .bids import ControlAction


@dataclass(frozen=True)
class OperatingState:
    base_case: PowerCase
    load_shed_mw: dict[int, float] = field(default_factory=dict)
    battery_injection_mw: dict[int, float] = field(default_factory=dict)
    generator_increase_mw: dict[int, float] = field(default_factory=dict)
    actions: tuple[ControlAction, ...] = ()

    def remaining_physical_load_mw(self, bus: int) -> float:
        return max(
            self.base_case.loads_mw.get(bus, 0.0) - self.load_shed_mw.get(bus, 0.0),
            0.0,
        )

    def remaining_net_load_mw(self, bus: int) -> float:
        return max(
            self.remaining_physical_load_mw(bus) - self.battery_injection_mw.get(bus, 0.0),
            0.0,
        )

    def apply(self, action: ControlAction) -> "OperatingState":
        if action.amount_mw <= 0:
            raise ValueError("Control action amount must be positive")
        load_shed = dict(self.load_shed_mw)
        battery = dict(self.battery_injection_mw)
        generator = dict(self.generator_increase_mw)
        if action.kind == "load_shed":
            load_shed[action.bus] = load_shed.get(action.bus, 0.0) + action.amount_mw
        elif action.kind == "battery_injection":
            battery[action.bus] = battery.get(action.bus, 0.0) + action.amount_mw
        elif action.kind == "generator_increase":
            if action.generator_id is None:
                raise ValueError("Generator action requires generator_id")
            generator[action.generator_id] = generator.get(action.generator_id, 0.0) + action.amount_mw
        else:
            raise ValueError(f"Unsupported action kind: {action.kind}")
        return replace(
            self,
            load_shed_mw=load_shed,
            battery_injection_mw=battery,
            generator_increase_mw=generator,
            actions=(*self.actions, action),
        )

    def to_power_case(self) -> PowerCase:
        loads = {
            bus: max(
                load
                - self.load_shed_mw.get(bus, 0.0)
                - self.battery_injection_mw.get(bus, 0.0),
                0.0,
            )
            for bus, load in self.base_case.loads_mw.items()
        }
        generators = tuple(
            replace(
                generator,
                scheduled_mw=min(
                    generator.scheduled_mw
                    + self.generator_increase_mw.get(generator.generator_id, 0.0),
                    generator.max_mw,
                ),
            )
            for generator in self.base_case.generators
        )
        return replace(self.base_case, loads_mw=loads, generators=generators)

    @property
    def preventive_load_shed_mw(self) -> float:
        return float(sum(self.load_shed_mw.values()))

    @property
    def battery_injection_total_mw(self) -> float:
        return float(sum(self.battery_injection_mw.values()))

    @property
    def generator_increase_total_mw(self) -> float:
        return float(sum(self.generator_increase_mw.values()))

    @property
    def intervention_cost(self) -> float:
        return float(sum(action.cost for action in self.actions))
