from __future__ import annotations

from cascade_ml.case_loader import load_pypower_case


def test_case39_is_loaded_from_pypower_with_stable_branch_ids() -> None:
    case = load_pypower_case("case39")

    assert len(case.buses) == 39
    assert len(case.branches) == 46
    assert case.branch_ids == tuple(range(46))
    assert case.base_mva == 100.0
    assert case.total_load_mw > 0
