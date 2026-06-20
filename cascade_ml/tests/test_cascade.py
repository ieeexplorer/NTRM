from __future__ import annotations

import pytest

from cascade_ml.cascade import simulate_cascade
from cascade_ml.model import Branch, Generator, PowerCase


def test_overload_trips_and_islands_load() -> None:
    case = PowerCase(
        name="overload",
        base_mva=100.0,
        buses=(1, 2, 3),
        loads_mw={1: 0.0, 2: 0.0, 3: 100.0},
        generators=(Generator(0, 1, 100.0, 100.0),),
        branches=(
            Branch(0, 1, 2, 0.1, 200.0),
            Branch(1, 2, 3, 0.1, 50.0),
        ),
    )

    result = simulate_cascade(case, ())

    assert len(result.steps) == 1
    assert result.steps[0].tripped_branch_ids == (1,)
    assert result.unserved_mw == pytest.approx(100.0)
    assert not result.terminated_by_limit


def test_unknown_branch_is_rejected() -> None:
    case = PowerCase(
        name="tiny",
        base_mva=100.0,
        buses=(1,),
        loads_mw={1: 0.0},
        generators=(),
        branches=(),
    )
    with pytest.raises(ValueError, match="Unknown branch"):
        simulate_cascade(case, (99,))
