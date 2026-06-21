"""Presentation helpers kept independent from Streamlit for easy testing."""

from __future__ import annotations

import pandas as pd

from .screening import ScreeningResult

FLAG_DESCRIPTIONS = {
    "aggregate_GB_data_mapped_to_synthetic_test_case": (
        "Aggregate GB demand is used only to scale a synthetic IEEE test network."
    ),
    "model_operating_range_requires_validation": (
        "A trained model must be validated across the displayed demand range."
    ),
    "invalid_newer_records_skipped": (
        "Newer source rows had invalid demand values, so the latest valid actual row was used."
    ),
    "demand_scale_clamped": "The demand multiplier was limited to the configured study range.",
    "stale_data": "The source observation is older than the configured freshness limit.",
    "forecast_record": "The selected source record is a forecast rather than an actual observation.",
    "future_observation": "The source timestamp is later than the retrieval timestamp.",
}


def format_age(age_hours: float) -> str:
    if age_hours < 1:
        return f"{max(round(age_hours * 60), 0)} min"
    if age_hours < 48:
        return f"{age_hours:.1f} h"
    return f"{age_hours / 24:.1f} days"


def describe_flag(flag: str) -> str:
    return FLAG_DESCRIPTIONS.get(flag, flag.replace("_", " ").capitalize() + ".")


def consequence_label(result: ScreeningResult) -> str:
    if result.severe_event:
        return "Severe simulated event"
    if result.simulated_unserved_mw > 0:
        return "Some simulated load loss"
    return "No simulated load loss"


def friendly_screening_frame(results: list[ScreeningResult]) -> pd.DataFrame:
    rows = []
    for rank, result in enumerate(results, start=1):
        rows.append(
            {
                "Rank": rank,
                "Outage branch IDs": result.contingency_key,
                "Assessment": consequence_label(result),
                "Conditional ML probability": result.conditional_probability,
                "Simulated unserved load (MW)": result.simulated_unserved_mw,
                "Unserved share (%)": 100 * result.simulated_unserved_fraction,
                "Cascade stages": result.cascade_generations,
            }
        )
    return pd.DataFrame(rows)
