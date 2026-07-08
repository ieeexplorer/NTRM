"""NESO CKAN connector for the daily demand update dataset."""

from __future__ import annotations

import csv
import logging
from datetime import datetime, timedelta, timezone
from io import StringIO
from zoneinfo import ZoneInfo

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..quality import assess_quality
from ..snapshot import OperatingSnapshot, utc_now

LOGGER = logging.getLogger(__name__)

INTERCONNECTOR_FIELDS = (
    "IFA_FLOW",
    "IFA2_FLOW",
    "BRITNED_FLOW",
    "MOYLE_FLOW",
    "EAST_WEST_FLOW",
    "NEMO_FLOW",
    "NSL_FLOW",
    "ELECLINK_FLOW",
    "VIKING_FLOW",
    "GREENLINK_FLOW",
)


class NesoDemandConnector:
    """Discover and fetch the latest actual NESO demand settlement record."""

    api_root = "https://api.neso.energy/api/3/action"
    package_id = "daily-demand-update"

    def __init__(
        self,
        *,
        timeout_seconds: float = 30.0,
        maximum_age_hours: float = 24 * 14,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.maximum_age_hours = maximum_age_hours
        self.session = session or _retrying_session()

    def fetch_latest_actual(self, *, retrieved_at: datetime | None = None) -> OperatingSnapshot:
        try:
            package_url = f"{self.api_root}/package_show?id={self.package_id}"
            package_response = self.session.get(package_url, timeout=self.timeout_seconds)
            package_response.raise_for_status()
            try:
                package_payload = package_response.json()
            except (ValueError, KeyError) as exc:
                raise ValueError(f"Invalid JSON response from NESO API: {exc}") from exc
            if not package_payload.get("success"):
                raise ValueError("NESO package lookup did not succeed")
            package = package_payload["result"]
            resources = [
                resource
                for resource in package.get("resources", [])
                if str(resource.get("format", "")).upper() == "CSV"
            ]
            if not resources:
                raise ValueError("NESO package contains no CSV resource")
            if len(resources) > 1:
                LOGGER.warning(
                    "NESO package has %d CSV resources; selecting the first (%s)",
                    len(resources),
                    resources[0].get("name", resources[0]["id"]),
                )
            resource = resources[0]
            csv_response = self.session.get(resource["url"], timeout=self.timeout_seconds)
            csv_response.raise_for_status()
            rows = list(csv.DictReader(StringIO(csv_response.text.lstrip("\ufeff"))))
            actual_rows = [
                row for row in rows if row.get("FORECAST_ACTUAL_INDICATOR", "").upper() == "A"
            ]
            if not actual_rows:
                raise ValueError("NESO dataset contains no actual demand records")
            valid_actual_rows = [row for row in actual_rows if _positive_demand(row)]
            if not valid_actual_rows:
                raise ValueError("NESO dataset contains no valid positive-demand actual records")
            row = max(valid_actual_rows, key=_settlement_key)
            retrieved = retrieved_at or utc_now()
            observed = _settlement_start_utc(row["SETTLEMENT_DATE"], int(row["SETTLEMENT_PERIOD"]))
            flags = list(
                assess_quality(
                    retrieved_at=retrieved,
                    observed_at=observed,
                    actual_or_forecast=row["FORECAST_ACTUAL_INDICATOR"],
                    maximum_age_hours=self.maximum_age_hours,
                )
            )
            invalid_count = len(actual_rows) - len(valid_actual_rows)
            if invalid_count > 0:
                flags.append("invalid_newer_records_skipped")
            return OperatingSnapshot(
                source="NESO Data Portal",
                dataset=package.get("title", self.package_id),
                resource_id=resource["id"],
                source_url=resource["url"],
                dataset_modified_at=package.get("metadata_modified"),
                retrieved_at=retrieved,
                observed_at=observed,
                settlement_date=row["SETTLEMENT_DATE"],
                settlement_period=int(row["SETTLEMENT_PERIOD"]),
                actual_or_forecast=row["FORECAST_ACTUAL_INDICATOR"],
                national_demand_mw=_required_float(row, "ND"),
                transmission_demand_mw=_optional_float(row, "TSD"),
                embedded_wind_mw=_optional_float(row, "EMBEDDED_WIND_GENERATION"),
                embedded_solar_mw=_optional_float(row, "EMBEDDED_SOLAR_GENERATION"),
                interconnector_flows_mw={
                    field: value
                    for field in INTERCONNECTOR_FIELDS
                    if (value := _optional_float(row, field)) is not None
                },
                quality_flags=tuple(flags),
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"NESO API request failed: {exc}") from exc


def _retrying_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "ntrm-research-demonstrator/0.1"})
    return session


def _settlement_key(row: dict[str, str]) -> tuple[str, int]:
    try:
        return row["SETTLEMENT_DATE"], int(row["SETTLEMENT_PERIOD"])
    except (KeyError, ValueError) as exc:
        raise ValueError("Malformed settlement row: missing or invalid date/period") from exc


def _settlement_start_utc(date_text: str, period: int) -> datetime:
    if period < 1 or period > 50:
        raise ValueError(f"Invalid settlement period: {period}")
    local_midnight = datetime.fromisoformat(date_text).replace(tzinfo=ZoneInfo("Europe/London"))
    settlement_day_start_utc = local_midnight.astimezone(timezone.utc)
    return settlement_day_start_utc + timedelta(minutes=30 * (period - 1))


def _required_float(row: dict[str, str], field: str) -> float:
    value = _optional_float(row, field)
    if value is None:
        raise ValueError(f"Missing required NESO field: {field}")
    return value


def _optional_float(row: dict[str, str], field: str) -> float | None:
    raw = row.get(field)
    if raw is None or not str(raw).strip():
        return None
    return float(raw)


def _positive_demand(row: dict[str, str]) -> bool:
    try:
        value = _optional_float(row, "ND")
    except ValueError:
        return False
    return value is not None and value > 0
