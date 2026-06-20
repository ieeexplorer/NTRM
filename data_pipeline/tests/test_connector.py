from __future__ import annotations

from datetime import datetime, timezone

from data_pipeline.connectors import NesoDemandConnector


class FakeResponse:
    def __init__(self, *, payload=None, text="") -> None:
        self.payload = payload
        self.text = text

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, package, csv_text) -> None:
        self.package = package
        self.csv_text = csv_text

    def get(self, url, timeout):
        if "package_show" in url:
            return FakeResponse(payload=self.package)
        return FakeResponse(text=self.csv_text)


def test_connector_discovers_resource_and_selects_latest_actual_record() -> None:
    package = {
        "success": True,
        "result": {
            "title": "Demand Data Update",
            "metadata_modified": "2026-06-20T08:20:08",
            "resources": [
                {"id": "resource-1", "format": "CSV", "url": "https://example.test/data.csv"}
            ],
        },
    }
    csv_text = """SETTLEMENT_DATE,SETTLEMENT_PERIOD,ND,FORECAST_ACTUAL_INDICATOR,TSD,EMBEDDED_WIND_GENERATION,EMBEDDED_SOLAR_GENERATION,IFA_FLOW
2026-06-18,1,20000,A,21000,1000,0,500
2026-06-19,2,22000,A,23000,1200,10,600
2026-06-20,2,0,A,500,0,0,0
2026-06-20,1,25000,F,26000,1300,20,700
"""
    connector = NesoDemandConnector(
        session=FakeSession(package, csv_text), maximum_age_hours=24 * 14
    )
    retrieved = datetime(2026, 6, 20, tzinfo=timezone.utc)

    snapshot = connector.fetch_latest_actual(retrieved_at=retrieved)

    assert snapshot.national_demand_mw == 22_000
    assert snapshot.settlement_date == "2026-06-19"
    assert snapshot.settlement_period == 2
    assert snapshot.actual_or_forecast == "A"
    assert snapshot.resource_id == "resource-1"
    assert snapshot.interconnector_flows_mw["IFA_FLOW"] == 600
    assert snapshot.quality_flags == ("invalid_newer_records_skipped",)
