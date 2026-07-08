"""Reproducible, unique contingency generation and labelled dataset creation."""

from __future__ import annotations

from functools import partial
from itertools import combinations
from random import Random

import joblib
import pandas as pd

from .cascade import simulate_cascade
from .features import extract_features
from .model import PowerCase

__all__ = ["build_dataset", "generate_contingencies"]


def generate_contingencies(
    branch_ids: tuple[int, ...],
    *,
    max_order: int = 3,
    n3_samples: int = 2_000,
    seed: int = 39,
) -> list[tuple[int, ...]]:
    """Enumerate N-1/N-2 and reproducibly sample unique N-3 contingencies."""

    if max_order < 1 or max_order > 3:
        raise ValueError("max_order must be between 1 and 3")
    contingencies: list[tuple[int, ...]] = []
    contingencies.extend(combinations(branch_ids, 1))
    if max_order >= 2:
        contingencies.extend(combinations(branch_ids, 2))
    if max_order >= 3:
        all_n3 = list(combinations(branch_ids, 3))
        sample_size = min(max(n3_samples, 0), len(all_n3))
        contingencies.extend(Random(seed).sample(all_n3, sample_size))
    return [tuple(item) for item in contingencies]


def _evaluate_contingency(
    case: PowerCase,
    contingency: tuple[int, ...],
    scenario_id: int,
    *,
    severe_threshold_fraction: float,
    overload_threshold: float,
) -> dict[str, float | int | str]:
    """Evaluate a single contingency and return a row dict for the dataset."""
    features = extract_features(case, contingency)
    result = simulate_cascade(case, contingency, overload_threshold=overload_threshold)
    unserved_fraction = result.unserved_mw / case.total_load_mw if case.total_load_mw else 0.0
    return {
        "scenario_id": scenario_id,
        "contingency_key": "|".join(map(str, contingency)),
        **features,
        "cascade_generations": len(result.steps),
        "final_unserved_mw": result.unserved_mw,
        "final_unserved_fraction": unserved_fraction,
        "severe_event": int(unserved_fraction >= severe_threshold_fraction),
        "terminated_by_limit": int(result.terminated_by_limit),
    }


def build_dataset(
    case: PowerCase,
    contingencies: list[tuple[int, ...]],
    *,
    severe_threshold_fraction: float = 0.2,
    overload_threshold: float = 1.0,
    n_jobs: int = 1,
) -> pd.DataFrame:
    """Build a labelled cascade scenario dataset.

    Parameters
    ----------
    n_jobs : int
        Number of parallel workers. 1 for sequential (default), -1 for all cores.
        Parallelism requires the PowerCase to be picklable.
    """
    if not 0 < severe_threshold_fraction <= 1:
        raise ValueError("severe_threshold_fraction must be in (0, 1]")

    evaluate_fn = partial(
        _evaluate_contingency,
        case,
        severe_threshold_fraction=severe_threshold_fraction,
        overload_threshold=overload_threshold,
    )

    if n_jobs == 1:
        rows = [
            evaluate_fn(contingency, scenario_id)
            for scenario_id, contingency in enumerate(contingencies)
        ]
    else:
        rows = joblib.Parallel(n_jobs=n_jobs, prefer="loky")(
            joblib.delayed(evaluate_fn)(contingency, scenario_id)
            for scenario_id, contingency in enumerate(contingencies)
        )

    return pd.DataFrame(rows)
