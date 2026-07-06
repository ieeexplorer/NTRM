from __future__ import annotations

import pytest
from ntrm_config import (
    NTRMConfig,
    _deep_update,
    load_config,
)


def test_load_config_returns_defaults_when_no_file(tmp_path, monkeypatch) -> None:
    """When no TOML file exists and CWD has no ntrm.toml, defaults are returned."""
    monkeypatch.chdir(tmp_path)
    config = load_config()

    assert isinstance(config, NTRMConfig)
    assert config.cascade.overload_threshold == 1.0
    assert config.cascade.max_generations == 20
    assert config.cascade.severe_threshold_fraction == pytest.approx(0.2)


def test_load_config_with_custom_toml(tmp_path, monkeypatch) -> None:
    toml_path = tmp_path / "custom.toml"
    toml_path.write_text(
        "[cascade]\n"
        "overload_threshold = 1.1\n"
        "max_generations = 10\n"
        "\n"
        "[model]\n"
        "n_estimators = 100\n"
        "seed = 42\n"
        "\n"
        "[controller]\n"
        "risk_threshold = 0.7\n"
        "target_loading_ratio = 0.85\n"
        "budget = 5000.0\n"
    )

    config = load_config(toml_path)

    assert config.cascade.overload_threshold == pytest.approx(1.1)
    assert config.cascade.max_generations == 10
    assert config.model.n_estimators == 100
    assert config.model.seed == 42
    assert config.controller.risk_threshold == pytest.approx(0.7)
    assert config.controller.target_loading_ratio == pytest.approx(0.85)
    assert config.controller.budget == pytest.approx(5000.0)
    # Unchanged fields keep defaults
    assert config.model.n_cv_splits == 5


def test_all_default_values_match_expected() -> None:
    config = NTRMConfig()

    # CascadeConfig defaults
    assert config.cascade.overload_threshold == 1.0
    assert config.cascade.max_generations == 20
    assert config.cascade.severe_threshold_fraction == pytest.approx(0.2)

    # ModelConfig defaults
    assert config.model.n_estimators == 400
    assert config.model.min_samples_leaf == 2
    assert config.model.n_cv_splits == 5
    assert config.model.classification_threshold == pytest.approx(0.5)
    assert config.model.n_jobs == -1
    assert config.model.seed == 39

    # ControllerConfig defaults
    assert config.controller.risk_threshold == pytest.approx(0.5)
    assert config.controller.target_loading_ratio == pytest.approx(0.9)
    assert config.controller.action_step_mw == pytest.approx(10.0)
    assert config.controller.duration_hours == pytest.approx(0.25)
    assert config.controller.maximum_actions == 100
    assert config.controller.budget is None

    # ResourceConfig defaults
    assert config.resources.max_shed_fraction == pytest.approx(0.1)
    assert config.resources.minimum_served_fraction == pytest.approx(0.8)
    assert config.resources.battery_max_power_mw == pytest.approx(50.0)
    assert config.resources.battery_energy_mwh == pytest.approx(25.0)
    assert config.resources.n_flex_load_agents == 3
    assert config.resources.n_battery_agents == 2

    # MappingConfigValues defaults
    assert config.mapping.reference_demand_mw == pytest.approx(30_000.0)
    assert config.mapping.minimum_scale == pytest.approx(0.75)
    assert config.mapping.maximum_scale == pytest.approx(1.25)


def test_deep_update_merges_nested_dicts() -> None:
    base = {"a": 1, "b": {"x": 10, "y": 20}, "c": 3}
    override = {"b": {"y": 99}, "d": 4}
    result = _deep_update(base, override)

    assert result == {"a": 1, "b": {"x": 10, "y": 99}, "c": 3, "d": 4}


def test_deep_update_does_not_mutate_base() -> None:
    base = {"a": {"x": 1}}
    override = {"a": {"y": 2}}
    result = _deep_update(base, override)

    assert base["a"] == {"x": 1}
    assert result["a"] == {"x": 1, "y": 2}


def test_deep_update_top_level_override() -> None:
    base = {"a": 1}
    override = {"a": 2}
    result = _deep_update(base, override)

    assert result["a"] == 2
