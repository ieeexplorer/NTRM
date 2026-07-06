from __future__ import annotations

import importlib.util
from pathlib import Path

from cascade_ml.model import Branch, Generator, PowerCase


def _load_train_model_script():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "train_model.py"
    spec = importlib.util.spec_from_file_location("train_model_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_multi_branch_sampling_is_unique_and_reproducible() -> None:
    script = _load_train_model_script()

    first = script.sample_multi_branch_contingencies(
        tuple(range(8)),
        sample_size=12,
        fail_min=3,
        max_failures=4,
        seed=42,
    )
    second = script.sample_multi_branch_contingencies(
        tuple(range(8)),
        sample_size=12,
        fail_min=3,
        max_failures=4,
        seed=42,
    )

    assert first == second
    assert len(first) == 12
    assert len(first) == len(set(first))
    assert all(3 <= len(contingency) <= 4 for contingency in first)


def test_build_cascade_event_dataset_uses_propagation_target() -> None:
    script = _load_train_model_script()
    case = PowerCase(
        name="triangle",
        base_mva=100.0,
        buses=(1, 2, 3),
        loads_mw={1: 0.0, 2: 0.0, 3: 100.0},
        generators=(Generator(0, 1, 100.0, 100.0),),
        branches=(
            Branch(0, 1, 2, 0.1, 200.0),
            Branch(1, 2, 3, 0.1, 50.0),
            Branch(2, 1, 3, 0.2, 200.0),
        ),
    )

    data = script.build_cascade_event_dataset(case, [(2,)], overload_threshold=1.0)

    assert data.loc[0, "contingency_key"] == "2"
    assert data.loc[0, "cascade_event"] == 1
    assert data.loc[0, "severe_event"] == 1
    assert data.loc[0, "cascade_generations"] >= 1
