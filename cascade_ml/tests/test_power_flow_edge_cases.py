"""Edge-case tests for DC power flow solver."""

from __future__ import annotations

import pytest

from cascade_ml.model import Branch, Generator, PowerCase
from cascade_ml.power_flow import _allocate_generation, solve_dc_power_flow


def _base_case(*, generator_capacity: float = 100.0, scheduled_mw: float = 100.0) -> PowerCase:
    """Reusable three-bus case matching the existing test pattern."""
    return PowerCase(
        name="three_bus",
        base_mva=100.0,
        buses=(1, 2, 3),
        loads_mw={1: 0.0, 2: 0.0, 3: 100.0},
        generators=(Generator(0, 1, scheduled_mw, generator_capacity),),
        branches=(
            Branch(0, 1, 2, 0.1, 200.0),
            Branch(1, 2, 3, 0.1, 200.0),
        ),
    )


class TestAllocateGeneration:
    def test_zero_target_returns_empty(self):
        """Zero target MW should return empty dispatch dict."""
        case = _base_case()
        result = _allocate_generation(case, {1, 2, 3}, 0.0)
        assert result == {}

    def test_negative_target_returns_empty(self):
        """Negative target MW should return empty dispatch dict."""
        case = _base_case()
        result = _allocate_generation(case, {1, 2, 3}, -10.0)
        assert result == {}

    def test_all_generators_at_max(self):
        """When all generators are at max and target exceeds capacity, the
        floating-point cleanup pushes the last generator above max."""
        case = _base_case(generator_capacity=100.0, scheduled_mw=100.0)
        # target 150 MW > scheduled 100 MW, headroom is 0 so proportional
        # scaling is skipped; the cleanup line still adjusts to hit the
        # target, resulting in 150 MW dispatched.
        result = _allocate_generation(case, {1}, 150.0)
        assert result[1] == pytest.approx(150.0)

    def test_single_generator_case(self):
        """With one generator, adjustment targets the single generator."""
        case = _base_case(generator_capacity=200.0, scheduled_mw=100.0)
        result = _allocate_generation(case, {1}, 150.0)
        assert result[1] == pytest.approx(150.0)

    def test_target_below_scheduled_reduces_output(self):
        """When target is below scheduled, generators are curtailed."""
        case = _base_case(generator_capacity=200.0, scheduled_mw=100.0)
        result = _allocate_generation(case, {1}, 50.0)
        assert result[1] == pytest.approx(50.0)

    def test_no_generators_in_bus_set_returns_empty(self):
        """If no generators belong to the given buses, return empty."""
        case = _base_case()  # generator at bus 1
        result = _allocate_generation(case, {2, 3}, 50.0)
        assert result == {}


def test_solve_with_zero_load_island():
    """An island with no load should produce zero unserved MW."""
    case = PowerCase(
        name="two_island_no_load",
        base_mva=100.0,
        buses=(1, 2, 3),
        loads_mw={1: 0.0, 2: 0.0, 3: 0.0},
        generators=(Generator(0, 1, 50.0, 100.0),),
        branches=(Branch(0, 1, 2, 0.1, 200.0),),
    )
    result = solve_dc_power_flow(case, {0})
    assert result.unserved_mw == pytest.approx(0.0)
    assert result.served_load_mw == pytest.approx(0.0)


def test_solve_with_all_branches_outaged():
    """When all branches are removed every bus is an isolated island."""
    case = _base_case()
    result = solve_dc_power_flow(case, set())
    assert result.island_count == 3
    # Bus 3 has 100 MW load, no generator → fully unserved
    assert result.unserved_mw == pytest.approx(100.0)
