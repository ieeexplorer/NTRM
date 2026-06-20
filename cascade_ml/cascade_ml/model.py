"""Small, explicit data model shared by the simulator and feature pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Branch:
    branch_id: int
    from_bus: int
    to_bus: int
    x_pu: float
    rate_mva: float


@dataclass(frozen=True)
class Generator:
    generator_id: int
    bus: int
    scheduled_mw: float
    max_mw: float


@dataclass(frozen=True)
class PowerCase:
    name: str
    base_mva: float
    buses: tuple[int, ...]
    loads_mw: dict[int, float]
    generators: tuple[Generator, ...]
    branches: tuple[Branch, ...]

    @property
    def total_load_mw(self) -> float:
        return float(sum(self.loads_mw.values()))

    @property
    def total_generation_capacity_mw(self) -> float:
        return float(sum(generator.max_mw for generator in self.generators))

    @property
    def branch_ids(self) -> tuple[int, ...]:
        return tuple(branch.branch_id for branch in self.branches)
