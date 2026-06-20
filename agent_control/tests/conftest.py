from __future__ import annotations

import pytest

from cascade_ml.model import Branch, Generator, PowerCase


@pytest.fixture
def overloaded_case() -> PowerCase:
    return PowerCase(
        name="overloaded_three_bus",
        base_mva=100.0,
        buses=(1, 2, 3),
        loads_mw={1: 0.0, 2: 0.0, 3: 100.0},
        generators=(Generator(0, 1, 100.0, 100.0),),
        branches=(
            Branch(0, 1, 2, 0.1, 80.0),
            Branch(1, 2, 3, 0.1, 80.0),
        ),
    )
