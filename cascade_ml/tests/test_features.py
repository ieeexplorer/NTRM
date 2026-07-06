from __future__ import annotations

from cascade_ml.case_loader import load_pypower_case
from cascade_ml.features import FEATURE_NAMES, FEATURE_VERSION, extract_features
from cascade_ml.model import Branch, PowerCase


def test_feature_names_is_tuple_of_fifteen_strings() -> None:
    assert isinstance(FEATURE_NAMES, tuple)
    assert len(FEATURE_NAMES) == 15
    assert all(isinstance(name, str) for name in FEATURE_NAMES)


def test_feature_version_is_string() -> None:
    assert isinstance(FEATURE_VERSION, str)


def test_extract_features_returns_keys_matching_feature_names() -> None:
    case = load_pypower_case("case39")
    features = extract_features(case, (0,))

    assert set(features.keys()) == set(FEATURE_NAMES)


def test_extract_features_returns_all_float_values() -> None:
    case = load_pypower_case("case39")
    features = extract_features(case, (0,))

    for key, value in features.items():
        assert isinstance(value, float), f"{key} is {type(value)}, expected float"


def test_extract_features_with_single_outage_on_case39() -> None:
    case = load_pypower_case("case39")
    features = extract_features(case, (0,))

    assert features["outage_count"] == 1.0
    assert features["active_branch_count"] == float(len(case.branches) - 1)
    assert features["island_count"] >= 1.0
    assert features["largest_component_fraction"] > 0.0


def test_extract_features_with_no_outage() -> None:
    case = load_pypower_case("case39")
    features = extract_features(case, ())

    assert features["outage_count"] == 0.0
    assert features["active_branch_count"] == float(len(case.branches))


def test_extract_features_with_empty_graph_all_branches_removed() -> None:
    """When every branch is outaged the graph has only isolated nodes."""
    case = PowerCase(
        name="tiny",
        base_mva=100.0,
        buses=(1, 2),
        loads_mw={1: 50.0, 2: 50.0},
        generators=(),
        branches=(Branch(0, 1, 2, 0.1, 200.0),),
    )

    features = extract_features(case, (0,))

    assert features["outage_count"] == 1.0
    assert features["active_branch_count"] == 0.0
    assert features["mean_degree"] == 0.0
    assert features["max_degree"] == 0.0
    assert features["mean_betweenness"] == 0.0
    assert features["max_betweenness"] == 0.0
    assert features["algebraic_connectivity"] == 0.0
    assert features["mean_line_loading"] == 0.0
    assert features["max_line_loading"] == 0.0
    assert features["std_line_loading"] == 0.0
