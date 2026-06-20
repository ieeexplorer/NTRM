from __future__ import annotations

from datetime import datetime, timezone

from data_pipeline.quality import assess_quality
from data_pipeline.snapshot import OperatingSnapshot


def example_snapshot() -> OperatingSnapshot:
    return OperatingSnapshot(
        source="test",
        dataset="demand",
        resource_id="r1",
        source_url="https://example.test",
        dataset_modified_at="2026-06-20T00:00:00",
        retrieved_at=datetime(2026, 6, 20, tzinfo=timezone.utc),
        observed_at=datetime(2026, 6, 19, 23, 30, tzinfo=timezone.utc),
        settlement_date="2026-06-20",
        settlement_period=1,
        actual_or_forecast="A",
        national_demand_mw=25_000,
        transmission_demand_mw=26_000,
        embedded_wind_mw=1_000,
        embedded_solar_mw=0,
        interconnector_flows_mw={"IFA_FLOW": 500},
    )


def test_snapshot_json_round_trip(tmp_path) -> None:
    path = tmp_path / "snapshot.json"
    example_snapshot().write_json(path)

    restored = OperatingSnapshot.read_json(path)

    assert restored == example_snapshot()


def test_quality_flags_stale_and_forecast_records() -> None:
    flags = assess_quality(
        retrieved_at=datetime(2026, 6, 20, tzinfo=timezone.utc),
        observed_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        actual_or_forecast="F",
        maximum_age_hours=24,
    )
    assert flags == ("forecast_record", "stale_data")
