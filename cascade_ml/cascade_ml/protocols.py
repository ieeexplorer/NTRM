"""Shared protocol definitions for the NTRM research demonstrator.

This module consolidates protocol definitions that were previously
duplicated across agent_control and data_pipeline packages.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .model import PowerCase


@runtime_checkable
class RiskPredictor(Protocol):
    """Protocol for ML-based cascade risk probability prediction."""

    def predict_probability(self, case: PowerCase, initial_outages: tuple[int, ...]) -> float: ...