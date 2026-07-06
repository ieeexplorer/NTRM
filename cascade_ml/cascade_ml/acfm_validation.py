"""Paired comparison metrics for DC-surrogate and AC-CFM scenario exports."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compare_results(
    dc: pd.DataFrame,
    ac: pd.DataFrame,
    *,
    dc_unserved_column: str = "final_unserved_mw",
    ac_unserved_column: str = "final_unserved_mw",
    dc_severe_column: str = "severe_event",
    ac_severe_column: str = "severe_event",
) -> tuple[dict, pd.DataFrame]:
    """Align unique contingencies and calculate transparent error metrics."""

    required_dc = {"contingency_key", dc_unserved_column, dc_severe_column}
    required_ac = {"contingency_key", ac_unserved_column, ac_severe_column}
    if missing := required_dc - set(dc.columns):
        raise ValueError(f"DC results are missing columns: {sorted(missing)}")
    if missing := required_ac - set(ac.columns):
        raise ValueError(f"AC-CFM results are missing columns: {sorted(missing)}")
    if dc["contingency_key"].duplicated().any() or ac["contingency_key"].duplicated().any():
        raise ValueError("Each input must contain one row per contingency_key")

    dc_view = dc[["contingency_key", dc_unserved_column, dc_severe_column]].rename(
        columns={dc_unserved_column: "dc_unserved_mw", dc_severe_column: "dc_severe"}
    )
    ac_view = ac[["contingency_key", ac_unserved_column, ac_severe_column]].rename(
        columns={ac_unserved_column: "ac_unserved_mw", ac_severe_column: "ac_severe"}
    )
    paired = dc_view.merge(ac_view, on="contingency_key", how="inner", validate="one_to_one")
    if paired.empty:
        raise ValueError("The DC and AC-CFM files contain no matching contingencies")
    paired["error_mw"] = paired["dc_unserved_mw"] - paired["ac_unserved_mw"]
    paired["absolute_error_mw"] = paired["error_mw"].abs()
    dc_label = paired["dc_severe"].astype(bool)
    ac_label = paired["ac_severe"].astype(bool)
    true_positive = int((dc_label & ac_label).sum())
    true_negative = int((~dc_label & ~ac_label).sum())
    false_positive = int((dc_label & ~ac_label).sum())
    false_negative = int((~dc_label & ac_label).sum())
    metrics = {
        "matched_scenarios": len(paired),
        "dc_only_scenarios": int(len(dc) - len(paired)),
        "ac_only_scenarios": int(len(ac) - len(paired)),
        "mean_absolute_error_mw": float(paired["absolute_error_mw"].mean()),
        "root_mean_squared_error_mw": float(np.sqrt(np.mean(np.square(paired["error_mw"])))),
        "mean_bias_mw": float(paired["error_mw"].mean()),
        "classification_agreement": float((dc_label == ac_label).mean()),
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "false_positive_rate": _safe_ratio(false_positive, false_positive + true_negative),
        "false_negative_rate": _safe_ratio(false_negative, false_negative + true_positive),
    }
    return metrics, paired


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    return float(numerator / denominator) if denominator else None
