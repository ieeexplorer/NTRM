from __future__ import annotations

import pandas as pd
import pytest

from cascade_ml.acfm_validation import compare_results


def test_validation_metrics_align_matching_contingencies() -> None:
    dc = pd.DataFrame(
        {
            "contingency_key": ["0|1", "0|2", "0|3"],
            "final_unserved_mw": [0.0, 100.0, 50.0],
            "severe_event": [0, 1, 1],
        }
    )
    ac = pd.DataFrame(
        {
            "contingency_key": ["0|1", "0|2", "0|3"],
            "final_unserved_mw": [0.0, 80.0, 0.0],
            "severe_event": [0, 1, 0],
        }
    )

    metrics, paired = compare_results(dc, ac)

    assert metrics["matched_scenarios"] == 3
    assert metrics["mean_absolute_error_mw"] == pytest.approx(70 / 3)
    assert metrics["classification_agreement"] == pytest.approx(2 / 3)
    assert metrics["false_positive"] == 1
    assert list(paired["error_mw"]) == [0.0, 20.0, 50.0]


def test_validation_rejects_duplicate_contingencies() -> None:
    duplicated = pd.DataFrame(
        {
            "contingency_key": ["0|1", "0|1"],
            "final_unserved_mw": [0.0, 0.0],
            "severe_event": [0, 0],
        }
    )
    with pytest.raises(ValueError, match="one row"):
        compare_results(duplicated, duplicated.drop_duplicates())
