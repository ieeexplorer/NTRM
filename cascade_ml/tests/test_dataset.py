from __future__ import annotations

from cascade_ml.dataset import generate_contingencies


def test_contingencies_are_unique_and_reproducible() -> None:
    first = generate_contingencies(tuple(range(5)), n3_samples=4, seed=7)
    second = generate_contingencies(tuple(range(5)), n3_samples=4, seed=7)

    assert first == second
    assert len(first) == 5 + 10 + 4
    assert len(first) == len(set(first))
    assert sum(len(item) == 1 for item in first) == 5
    assert sum(len(item) == 2 for item in first) == 10
