from __future__ import annotations

from test_snapshot import example_snapshot

from cascade_ml.model import Branch, Generator, PowerCase
from data_pipeline.case_mapping import MappingConfig
from data_pipeline.risk_service import assess_snapshot


class FixedPredictor:
    def __init__(self, probability: float) -> None:
        self.probability = probability

    def predict_probability(self, case, initial_outages) -> float:
        return self.probability


def test_model_probability_gates_simulated_control() -> None:
    case = PowerCase(
        name="two_bus",
        base_mva=100,
        buses=(1, 2),
        loads_mw={1: 0, 2: 100},
        generators=(Generator(0, 1, 100, 100),),
        branches=(Branch(0, 1, 2, 0.1, 80),),
    )

    report = assess_snapshot(
        example_snapshot(),
        case,
        [(0,)],
        predictor=FixedPredictor(0.1),
        mapping_config=MappingConfig(reference_demand_mw=25_000),
        control_risk_threshold=0.5,
    )

    assert report.screening[0].conditional_probability == 0.1
    assert report.simulated_intervention is None
