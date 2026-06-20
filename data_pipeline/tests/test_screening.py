from __future__ import annotations

import pytest

from cascade_ml.model import Branch, Generator, PowerCase
from data_pipeline.screening import screen_contingencies


def test_screening_reports_conditional_simulation_not_universal_risk() -> None:
    case = PowerCase(
        name="three_bus",
        base_mva=100,
        buses=(1, 2, 3),
        loads_mw={1: 0, 2: 0, 3: 100},
        generators=(Generator(0, 1, 100, 100),),
        branches=(
            Branch(0, 1, 2, 0.1, 200),
            Branch(1, 2, 3, 0.1, 200),
        ),
    )

    results = screen_contingencies(case, [(0,), (1,)])

    assert len(results) == 2
    assert all(result.conditional_probability is None for result in results)
    assert all(result.simulated_unserved_mw == pytest.approx(100) for result in results)
    assert all(result.severe_event for result in results)
