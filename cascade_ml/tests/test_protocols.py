"""Tests for the shared protocols module."""

from __future__ import annotations

from cascade_ml.protocols import RiskPredictor


class _ValidPredictor:
    """A concrete class satisfying the RiskPredictor protocol."""

    def predict_probability(self, case, initial_outages: tuple[int, ...]) -> float:
        return 0.5


def test_valid_predictor_satisfies_protocol():
    predictor = _ValidPredictor()
    assert isinstance(predictor, RiskPredictor)


def test_missing_method_does_not_satisfy_protocol():
    class _InvalidPredictor:
        pass

    assert not isinstance(_InvalidPredictor(), RiskPredictor)
