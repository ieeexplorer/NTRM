from __future__ import annotations

import pytest

from cascade_ml.model import Branch, Generator, PowerCase
from data_pipeline.case_mapping import MappingConfig, map_snapshot_to_case
from test_snapshot import example_snapshot


def base_case() -> PowerCase:
    return PowerCase(
        name="two_bus",
        base_mva=100,
        buses=(1, 2),
        loads_mw={1: 0, 2: 100},
        generators=(Generator(0, 1, 100, 150),),
        branches=(Branch(0, 1, 2, 0.1, 200),),
    )


def test_mapping_scales_synthetic_load_and_preserves_provenance_warning() -> None:
    report = map_snapshot_to_case(
        example_snapshot(),
        base_case(),
        MappingConfig(reference_demand_mw=20_000, minimum_scale=0.5, maximum_scale=2.0),
    )
    assert report.applied_demand_scale == pytest.approx(1.25)
    assert report.case.loads_mw[2] == pytest.approx(125)
    assert "aggregate_GB_data_mapped_to_synthetic_test_case" in report.warnings


def test_mapping_clamps_out_of_range_conditions() -> None:
    report = map_snapshot_to_case(
        example_snapshot(),
        base_case(),
        MappingConfig(reference_demand_mw=10_000, minimum_scale=0.75, maximum_scale=1.2),
    )
    assert report.raw_demand_scale == pytest.approx(2.5)
    assert report.applied_demand_scale == pytest.approx(1.2)
    assert report.clamped
    assert "demand_scale_clamped" in report.warnings
