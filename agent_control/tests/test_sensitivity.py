from __future__ import annotations

from agent_control.resources import BatteryAgent, GeneratorAgent
from agent_control.sensitivity import PortfolioConfig, build_portfolio, standard_portfolios


def test_standard_portfolios_change_available_resources(overloaded_case) -> None:
    full = build_portfolio(overloaded_case, PortfolioConfig("full"))
    load_only = build_portfolio(
        overloaded_case,
        PortfolioConfig("load_only", include_batteries=False, include_generators=False),
    )

    assert not any(isinstance(agent, BatteryAgent) for agent in load_only)
    assert not any(isinstance(agent, GeneratorAgent) for agent in load_only)
    assert len(full) >= len(load_only)
    assert len(standard_portfolios()) == 4
