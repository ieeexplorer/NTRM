from __future__ import annotations

import pytest

from data_pipeline.dashboard_view import describe_flag, format_age, friendly_screening_frame
from data_pipeline.screening import ScreeningResult


def test_dashboard_helpers_use_plain_language() -> None:
    result = ScreeningResult("0|2", (0, 2), None, 100.0, 0.05, 1, False)
    frame = friendly_screening_frame([result])

    assert format_age(0.5) == "30 min"
    assert format_age(72) == "3.0 days"
    assert frame.loc[0, "Assessment"] == "Some simulated load loss"
    assert frame.loc[0, "Unserved share (%)"] == pytest.approx(5.0)
    assert "synthetic IEEE" in describe_flag("aggregate_GB_data_mapped_to_synthetic_test_case")
