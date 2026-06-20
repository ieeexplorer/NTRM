"""Versionable operating snapshot with provenance and quality metadata."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class OperatingSnapshot:
    source: str
    dataset: str
    resource_id: str
    source_url: str
    dataset_modified_at: str | None
    retrieved_at: datetime
    observed_at: datetime
    settlement_date: str
    settlement_period: int
    actual_or_forecast: str
    national_demand_mw: float
    transmission_demand_mw: float | None
    embedded_wind_mw: float | None
    embedded_solar_mw: float | None
    interconnector_flows_mw: dict[str, float]
    quality_flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.retrieved_at.tzinfo is None or self.observed_at.tzinfo is None:
            raise ValueError("Snapshot timestamps must be timezone-aware")
        if self.national_demand_mw <= 0:
            raise ValueError("National demand must be positive")

    @property
    def age_hours(self) -> float:
        return (self.retrieved_at - self.observed_at).total_seconds() / 3_600

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["retrieved_at"] = self.retrieved_at.isoformat()
        payload["observed_at"] = self.observed_at.isoformat()
        payload["quality_flags"] = list(self.quality_flags)
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> "OperatingSnapshot":
        values = dict(payload)
        values["retrieved_at"] = datetime.fromisoformat(values["retrieved_at"])
        values["observed_at"] = datetime.fromisoformat(values["observed_at"])
        values["quality_flags"] = tuple(values.get("quality_flags", ()))
        return cls(**values)

    def write_json(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> "OperatingSnapshot":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
