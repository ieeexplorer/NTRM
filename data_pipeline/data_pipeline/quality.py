"""Transparent quality flags for public operating data."""

from __future__ import annotations

from datetime import datetime


def assess_quality(
    *,
    retrieved_at: datetime,
    observed_at: datetime,
    actual_or_forecast: str,
    maximum_age_hours: float,
) -> tuple[str, ...]:
    flags: list[str] = []
    age_hours = (retrieved_at - observed_at).total_seconds() / 3_600
    if actual_or_forecast.upper() != "A":
        flags.append("forecast_record")
    if age_hours < -1:
        flags.append("future_observation")
    elif age_hours > maximum_age_hours:
        flags.append("stale_data")
    return tuple(flags)
