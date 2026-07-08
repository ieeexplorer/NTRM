"""Edge-case tests for NESO connector helpers."""

from __future__ import annotations

import pytest

from data_pipeline.connectors.neso import (
    _optional_float,
    _positive_demand,
    _settlement_key,
    _settlement_start_utc,
)


class TestSettlementKey:
    def test_valid_row(self):
        row = {"SETTLEMENT_DATE": "2024-01-15", "SETTLEMENT_PERIOD": "24"}
        assert _settlement_key(row) == ("2024-01-15", 24)

    def test_missing_period_raises(self):
        with pytest.raises((ValueError, KeyError)):
            _settlement_key({"SETTLEMENT_DATE": "2024-01-15"})

    def test_invalid_period_raises(self):
        with pytest.raises(ValueError):
            _settlement_key({"SETTLEMENT_DATE": "2024-01-15", "SETTLEMENT_PERIOD": "abc"})


class TestOptionalFloat:
    def test_none_returns_none(self):
        assert _optional_float({}, "ND") is None

    def test_empty_string_returns_none(self):
        assert _optional_float({"ND": ""}, "ND") is None

    def test_whitespace_returns_none(self):
        assert _optional_float({"ND": "  "}, "ND") is None

    def test_valid_float(self):
        assert _optional_float({"ND": "1234.5"}, "ND") == 1234.5

    def test_negative_value(self):
        assert _optional_float({"ND": "-100"}, "ND") == -100.0


class TestPositiveDemand:
    def test_positive_returns_true(self):
        assert _positive_demand({"ND": "1000"}) is True

    def test_zero_returns_false(self):
        assert _positive_demand({"ND": "0"}) is False

    def test_negative_returns_false(self):
        assert _positive_demand({"ND": "-100"}) is False

    def test_missing_returns_false(self):
        assert _positive_demand({}) is False

    def test_invalid_returns_false(self):
        assert _positive_demand({"ND": "not_a_number"}) is False


class TestSettlementStartUtc:
    def test_period_1_is_midnight(self):
        dt = _settlement_start_utc("2024-01-15", 1)
        # In January (GMT, not BST) period 1 starts at 00:00 UTC.
        assert dt.hour == 0
        assert dt.minute == 0

    def test_period_2_is_half_hour(self):
        dt = _settlement_start_utc("2024-01-15", 2)
        assert dt.hour == 0
        assert dt.minute == 30

    def test_invalid_period_low_raises(self):
        with pytest.raises(ValueError):
            _settlement_start_utc("2024-01-15", 0)

    def test_invalid_period_high_raises(self):
        with pytest.raises(ValueError):
            _settlement_start_utc("2024-01-15", 51)