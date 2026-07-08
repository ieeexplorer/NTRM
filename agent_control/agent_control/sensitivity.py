"""Reproducible resource-portfolio sensitivity helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from cascade_ml.model import PowerCase

from .resources import BatteryAgent, FlexibleLoadAgent, GeneratorAgent, ResourceAgent

if TYPE_CHECKING:
    from ntrm_config import ResourceConfig


@dataclass(frozen=True)
class PortfolioConfig:
    name: str
    include_flexible_load: bool = True
    include_batteries: bool = True
    include_generators: bool = True
    battery_capacity_scale: float = 1.0


def build_portfolio(
    case: PowerCase,
    config: PortfolioConfig,
    resource_config: "ResourceConfig | None" = None,
) -> list[ResourceAgent]:
    """Construct a synthetic, documented resource portfolio for comparison."""

    if config.battery_capacity_scale < 0:
        raise ValueError("battery_capacity_scale cannot be negative")

    # Defaults matching the original hardcoded values.
    n_flex = resource_config.n_flex_load_agents if resource_config else 3
    max_shed_frac = resource_config.max_shed_fraction if resource_config else 0.1
    min_served_frac = resource_config.minimum_served_fraction if resource_config else 0.8
    flex_cost = resource_config.flex_load_cost_per_mwh if resource_config else 1_000.0

    n_bat = resource_config.n_battery_agents if resource_config else 2
    bat_max_power = resource_config.battery_max_power_mw if resource_config else 50.0
    bat_energy = resource_config.battery_energy_mwh if resource_config else 25.0
    bat_soc = resource_config.battery_initial_soc if resource_config else 0.8
    bat_eff = resource_config.battery_discharge_efficiency if resource_config else 0.95
    bat_cost = resource_config.battery_cost_per_mwh if resource_config else 50.0

    gen_max_inc = resource_config.generator_max_increase_mw if resource_config else 50.0
    gen_ramp = resource_config.generator_ramp_mw_per_min if resource_config else 10.0
    gen_resp = resource_config.generator_response_minutes if resource_config else 5.0
    gen_cost = resource_config.generator_cost_per_mwh if resource_config else 100.0

    load_buses = sorted(case.loads_mw, key=lambda bus: case.loads_mw[bus], reverse=True)
    agents: list[ResourceAgent] = []
    if config.include_flexible_load:
        for bus in load_buses[:n_flex]:
            load = case.loads_mw[bus]
            agents.append(
                FlexibleLoadAgent(
                    f"flex-{bus}",
                    bus,
                    max_shed_frac * load,
                    minimum_served_mw=min_served_frac * load,
                    cost_per_mwh=flex_cost,
                )
            )
    if config.include_batteries and config.battery_capacity_scale > 0:
        for bus in load_buses[n_flex : n_flex + n_bat]:
            agents.append(
                BatteryAgent(
                    f"battery-{bus}",
                    bus,
                    max_power_mw=bat_max_power * config.battery_capacity_scale,
                    energy_capacity_mwh=bat_energy * config.battery_capacity_scale,
                    state_of_charge=bat_soc,
                    discharge_efficiency=bat_eff,
                    cost_per_mwh=bat_cost,
                )
            )
    if config.include_generators:
        for generator in case.generators:
            if generator.max_mw > generator.scheduled_mw:
                agents.append(
                    GeneratorAgent(
                        f"generator-{generator.generator_id}",
                        generator.generator_id,
                        gen_max_inc,
                        gen_ramp,
                        gen_resp,
                        cost_per_mwh=gen_cost,
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
