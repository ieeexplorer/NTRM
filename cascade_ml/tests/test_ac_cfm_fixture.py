from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "case39_ac_cfm_n1_schema.json"
REQUIRED_METADATA = {
    "case",
    "n_buses",
    "n_branches",
    "n_contingencies",
    "contingency_type",
    "branch_indexing",
    "solver",
    "matlab_function",
    "generated_at",
    "matpower_version",
}
REQUIRED_CONTINGENCY_FIELDS = {
    "branch_idx",
    "matlab_branch_row",
    "from_bus",
    "to_bus",
    "ac_branch_loadings_mw",
    "ac_cascade_flag",
    "ac_unserved_mw",
}


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_case39_ac_cfm_schema_placeholder_metadata() -> None:
    payload = _load_fixture()
    metadata = payload["metadata"]

    assert set(metadata) >= REQUIRED_METADATA
    assert metadata["case"] == "case39"
    assert metadata["n_buses"] == 39
    assert metadata["n_branches"] == 46
    assert metadata["n_contingencies"] == 46
    assert metadata["contingency_type"] == "N-1_single_branch"
    assert metadata["branch_indexing"] == "zero_based"
    assert metadata["solver"] == "AC-CFM"
    assert isinstance(payload["contingencies"], list)


def test_case39_ac_cfm_fixture_entries_when_populated() -> None:
    payload = _load_fixture()
    contingencies = payload["contingencies"]
    if not contingencies:
        pytest.skip("AC-CFM case39 N-1 results have not been generated yet")

    assert len(contingencies) == payload["metadata"]["n_contingencies"]
    seen: set[int] = set()
    for row in contingencies:
        assert set(row) >= REQUIRED_CONTINGENCY_FIELDS
        assert row["branch_idx"] not in seen
        seen.add(row["branch_idx"])
        assert row["branch_idx"] + 1 == row["matlab_branch_row"]
        assert isinstance(row["ac_branch_loadings_mw"], list)
        assert len(row["ac_branch_loadings_mw"]) == payload["metadata"]["n_branches"]
        assert isinstance(row["ac_cascade_flag"], bool)
        assert row["ac_unserved_mw"] >= 0.0
