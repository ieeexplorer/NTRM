from __future__ import annotations

import pytest

from cascade_ml.model import Branch, Generator, PowerCase
from cascade_ml.power_flow import solve_dc_power_flow


def three_bus_case(*, generator_capacity: float = 100.0) -> PowerCase:
    return PowerCase(
        name="three_bus",
        base_mva=100.0,
        buses=(1, 2, 3),
        loads_mw={1: 0.0, 2: 0.0, 3: 100.0},
        generators=(Generator(0, 1, 100.0, generator_capacity),),
        branches=(
            Branch(0, 1, 2, 0.1, 200.0),
            Branch(1, 2, 3, 0.1, 200.0),
        ),
    )


def test_dc_power_flow_preserves_mw_and_per_unit_scaling() -> None:
    result = solve_dc_power_flow(three_bus_case(), {0, 1})

    assert result.unserved_mw == pytest.approx(0.0)
    assert abs(result.flows_mw[0]) == pytest.approx(100.0)
    assert abs(result.flows_mw[1]) == pytest.approx(100.0)
    assert result.loading_ratios[0] == pytest.approx(0.5)


def test_island_without_enough_generation_sheds_load() -> None:
    result = solve_dc_power_flow(three_bus_case(generator_capacity=60.0), {0, 1})

    assert result.served_load_mw == pytest.approx(60.0)
    assert result.unserved_mw == pytest.approx(40.0)
    assert abs(result.flows_mw[0]) == pytest.approx(60.0)


def test_disconnected_load_is_fully_unserved() -> None:
    result = solve_dc_power_flow(three_bus_case(), {0})

    assert result.island_count == 2
    assert result.unserved_mw == pytest.approx(100.0)
