"""Streamlit view for saved, reproducible research snapshots."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from cascade_ml.case_loader import load_pypower_case
from cascade_ml.dataset import generate_contingencies
from data_pipeline.risk_service import assess_snapshot
from data_pipeline.screening import screening_frame
from data_pipeline.snapshot import OperatingSnapshot

st.set_page_config(page_title="NTRM Research Demonstrator", layout="wide")
st.title("Public-data-informed cascade research demonstrator")
st.error("Synthetic IEEE test-system study — not a model of the GB network and not operational advice.")

snapshot_path = Path(st.sidebar.text_input("Snapshot JSON", "snapshots/latest.json"))
contingency_limit = st.sidebar.slider("N-1 contingencies", 1, 46, 10)
if not snapshot_path.exists():
    st.info("Fetch or select a saved snapshot to begin.")
    st.stop()

snapshot = OperatingSnapshot.read_json(snapshot_path)
case = load_pypower_case("case39")
report = assess_snapshot(
    snapshot,
    case,
    generate_contingencies(case.branch_ids, max_order=1)[:contingency_limit],
)

left, middle, right = st.columns(3)
left.metric("NESO national demand", f"{snapshot.national_demand_mw:,.0f} MW")
middle.metric("Observation", snapshot.observed_at.isoformat())
right.metric("Synthetic demand scale", f"{report.mapping.applied_demand_scale:.3f}")
if snapshot.quality_flags:
    st.warning("Data-quality flags: " + ", ".join(snapshot.quality_flags))
st.caption("Mapping warnings: " + ", ".join(report.mapping.warnings))

st.subheader("Conditional contingency screening")
st.dataframe(screening_frame(list(report.screening)), use_container_width=True)
if report.simulated_intervention:
    outcome = report.simulated_intervention
    st.subheader("Simulated intervention for highest-ranked contingency")
    st.write(
        {
            "preventive_load_shed_mw": outcome.preventive_load_shed_mw,
            "controlled_unserved_mw": outcome.controlled_unserved_mw,
            "action_count": outcome.action_count,
            "intervention_cost_units": outcome.intervention_cost,
        }
    )
