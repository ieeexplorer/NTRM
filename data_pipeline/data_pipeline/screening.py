"""Conditional contingency screening for a synthetic operating case."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

import pandas as pd

from cascade_ml.cascade import simulate_cascade
from cascade_ml.model import PowerCase


class RiskPredictor(Protocol):
    def predict_probability(self, case: PowerCase, initial_outages: tuple[int, ...]) -> float: ...


@dataclass(frozen=True)
class ScreeningResult:
    contingency_key: str
    outage_branch_ids: tuple[int, ...]
    conditional_probability: float | None
    simulated_unserved_mw: float
    simulated_unserved_fraction: float
    cascade_generations: int
    severe_event: bool


def screen_contingencies(
    case: PowerCase,
    contingencies: list[tuple[int, ...]],
    *,
    predictor: RiskPredictor | None = None,
    severe_threshold_fraction: float = 0.2,
) -> list[ScreeningResult]:
    results = []
    for contingency in contingencies:
        cascade = simulate_cascade(case, contingency)
        fraction = cascade.unserved_mw / case.total_load_mw if case.total_load_mw else 0.0
        probability = (
            predictor.predict_probability(case, contingency) if predictor is not None else None
        )
        results.append(
            ScreeningResult(
                contingency_key="|".join(map(str, contingency)),
                outage_branch_ids=contingency,
                conditional_probability=probability,
                simulated_unserved_mw=cascade.unserved_mw,
                simulated_unserved_fraction=fraction,
                cascade_generations=len(cascade.steps),
                severe_event=fraction >= severe_threshold_fraction,
            )
        )
    return sorted(
        results,
        key=lambda result: (
            result.conditional_probability
            if result.conditional_probability is not None
            else result.simulated_unserved_fraction
        ),
        reverse=True,
    )


def screening_frame(results: list[ScreeningResult]) -> pd.DataFrame:
    rows = []
    for result in results:
        row = asdict(result)
        row["outage_branch_ids"] = "|".join(map(str, result.outage_branch_ids))
        rows.append(row)
    return pd.DataFrame(rows)
