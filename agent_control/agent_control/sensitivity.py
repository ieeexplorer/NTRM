"""Reproducible resource-portfolio sensitivity helpers."""

from __future__ import annotations

from dataclasses import dataclass

from cascade_ml.model import PowerCase

from .resources import BatteryAgent, FlexibleLoadAgent, GeneratorAgent


@dataclass(frozen=True)
class PortfolioConfig:
    name: str
    include_flexible_load: bool = True
    include_batteries: bool = True
    include_generators: bool = True
    battery_capacity_scale: float = 1.0


def build_portfolio(case: PowerCase, config: PortfolioConfig):
    """Construct a synthetic, documented resource portfolio for comparison."""

    if config.battery_capacity_scale < 0:
        raise ValueError("battery_capacity_scale cannot be negative")
    load_buses = sorted(case.loads_mw, key=case.loads_mw.get, reverse=True)
    agents = []
    if config.include_flexible_load:
        for bus in load_buses[:3]:
            load = case.loads_mw[bus]
            agents.append(
                FlexibleLoadAgent(
                    f"flex-{bus}", bus, min(50.0, 0.1 * load), minimum_served_mw=0.8 * load
                )
            )
    if config.include_batteries and config.battery_capacity_scale > 0:
        for bus in load_buses[3:5]:
            agents.append(
                BatteryAgent(
                    f"battery-{bus}",
                    bus,
                    max_power_mw=50.0 * config.battery_capacity_scale,
                    energy_capacity_mwh=25.0 * config.battery_capacity_scale,
                    state_of_charge=0.8,
                )
            )
    if config.include_generators:
        for generator in case.generators:
            if generator.max_mw > generator.scheduled_mw:
                agents.append(
                    GeneratorAgent(
                        f"generator-{generator.generator_id}",
                        generator.generator_id,
                        50.0,
                        10.0,
                        5.0,
                    )
                )
    return agents


def standard_portfolios() -> tuple[PortfolioConfig, ...]:
    return (
        PortfolioConfig("full_portfolio"),
        PortfolioConfig("half_battery", battery_capacity_scale=0.5),
        PortfolioConfig("no_battery", include_batteries=False),
        PortfolioConfig("flexible_load_only", include_batteries=False, include_generators=False),
    )
