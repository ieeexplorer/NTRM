"""Map aggregate public demand to a bounded synthetic IEEE test-case condition."""

from __future__ import annotations

from dataclasses import dataclass, replace

from cascade_ml.model import PowerCase

from .snapshot import OperatingSnapshot


@dataclass(frozen=True)
class MappingConfig:
    reference_demand_mw: float = 30_000.0
    minimum_scale: float = 0.75
    maximum_scale: float = 1.25

    def __post_init__(self) -> None:
        if self.reference_demand_mw <= 0:
            raise ValueError("reference_demand_mw must be positive")
        if not 0 < self.minimum_scale <= self.maximum_scale:
            raise ValueError("invalid mapping scale bounds")


@dataclass(frozen=True)
class MappingReport:
    case: PowerCase
    raw_demand_scale: float
    applied_demand_scale: float
    clamped: bool
    warnings: tuple[str, ...]


def map_snapshot_to_case(
    snapshot: OperatingSnapshot,
    base_case: PowerCase,
    config: MappingConfig | None = None,
) -> MappingReport:
    """Create a synthetic operating condition, not a model of the GB network."""

    config = config or MappingConfig()
    raw_scale = snapshot.national_demand_mw / config.reference_demand_mw
    applied_scale = min(max(raw_scale, config.minimum_scale), config.maximum_scale)
    clamped = applied_scale != raw_scale
    warnings = [
        "aggregate_GB_data_mapped_to_synthetic_test_case",
        "model_operating_range_requires_validation",
    ]
    warnings.extend(snapshot.quality_flags)
    if clamped:
        warnings.append("demand_scale_clamped")
    mapped = replace(
        base_case,
        name=f"{base_case.name}-synthetic-{snapshot.settlement_date}-sp{snapshot.settlement_period}",
        loads_mw={bus: load * applied_scale for bus, load in base_case.loads_mw.items()},
    )
    return MappingReport(
        case=mapped,
        raw_demand_scale=raw_scale,
        applied_demand_scale=applied_scale,
        clamped=clamped,
        warnings=tuple(dict.fromkeys(warnings)),
    )
