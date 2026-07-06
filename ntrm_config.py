"""Centralised configuration for the NTRM research demonstrator.

Load with:
    from ntrm_config import load_config
    config = load_config()          # reads ntrm.toml from CWD or package
    config = load_config("path/to/custom.toml")
"""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "ntrm.toml"


@dataclass(frozen=True)
class CascadeConfig:
    """Parameters for DC cascade simulation."""

    overload_threshold: float = 1.0
    max_generations: int = 20
    severe_threshold_fraction: float = 0.2


@dataclass(frozen=True)
class ModelConfig:
    """Parameters for ML model training."""

    n_estimators: int = 400
    min_samples_leaf: int = 2
    n_cv_splits: int = 5
    classification_threshold: float = 0.5
    n_jobs: int = -1
    seed: int = 39


@dataclass(frozen=True)
class ControllerConfig:
    """Parameters for the network-aware controller."""

    target_loading_ratio: float = 0.9
    action_step_mw: float = 10.0
    duration_hours: float = 0.25
    maximum_actions: int = 100
    budget: float | None = None
    tolerance: float = 1e-12


@dataclass(frozen=True)
class ResourceConfig:
    """Parameters for synthetic resource portfolios."""

    max_shed_fraction: float = 0.1
    minimum_served_fraction: float = 0.8
    battery_max_power_mw: float = 50.0
    battery_energy_mwh: float = 25.0
    battery_initial_soc: float = 0.8
    battery_discharge_efficiency: float = 0.95
    generator_max_increase_mw: float = 50.0
    generator_ramp_mw_per_min: float = 10.0
    generator_response_minutes: float = 5.0
    flex_load_cost_per_mwh: float = 1_000.0
    battery_cost_per_mwh: float = 50.0
    generator_cost_per_mwh: float = 100.0
    n_flex_load_agents: int = 3
    n_battery_agents: int = 2


@dataclass(frozen=True)
class MappingConfigValues:
    """Parameters for NESO-to-synthetic demand mapping."""

    reference_demand_mw: float = 30_000.0
    minimum_scale: float = 0.75
    maximum_scale: float = 1.25


@dataclass(frozen=True)
class NTRMConfig:
    """Top-level configuration aggregating all sub-configs."""

    cascade: CascadeConfig = field(default_factory=CascadeConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    controller: ControllerConfig = field(default_factory=ControllerConfig)
    resources: ResourceConfig = field(default_factory=ResourceConfig)
    mapping: MappingConfigValues = field(default_factory=MappingConfigValues)


def _deep_update(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_update(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path | None = None) -> NTRMConfig:
    """Load configuration from a TOML file, falling back to defaults.

    Parameters
    ----------
    path : str | Path | None
        Explicit path to a ``ntrm.toml`` file.  If *None*, looks for
        ``./ntrm.toml`` then the package-bundled default.
    """
    search_paths: list[Path] = []
    if path is not None:
        search_paths.append(Path(path))
    else:
        search_paths.append(Path.cwd() / "ntrm.toml")
        search_paths.append(_DEFAULT_CONFIG_PATH)

    for candidate in search_paths:
        if candidate.exists():
            LOGGER.info("Loading configuration from %s", candidate)
            with open(candidate, "rb") as f:
                raw = tomllib.load(f)
            return _build_config(raw)

    LOGGER.info("No ntrm.toml found; using built-in defaults")
    return NTRMConfig()


def _build_config(raw: dict[str, Any]) -> NTRMConfig:
    """Convert a raw TOML dict into an NTRMConfig dataclass."""
    cascade_raw = raw.get("cascade", {})
    model_raw = raw.get("model", {})
    controller_raw = raw.get("controller", {})
    resources_raw = raw.get("resources", {})
    mapping_raw = raw.get("mapping", {})

    return NTRMConfig(
        cascade=CascadeConfig(**cascade_raw),
        model=ModelConfig(**model_raw),
        controller=ControllerConfig(**controller_raw),
        resources=ResourceConfig(**resources_raw),
        mapping=MappingConfigValues(**mapping_raw),
    )