"""Understandable Streamlit interface for the NTRM research demonstrator."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

import streamlit as st

# Resolve the example snapshot relative to this file.
_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_SNAPSHOT = _ROOT / "data_pipeline" / "examples" / "neso_snapshot_example.json"
for _module_directory in ("cascade_ml", "agent_control", "data_pipeline"):
    module_path = str(_ROOT / _module_directory)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)

from agent_control.predictor import ModelBundlePredictor  # noqa: E402
from cascade_ml.case_loader import load_pypower_case  # noqa: E402
from cascade_ml.dataset import generate_contingencies  # noqa: E402
from data_pipeline.case_mapping import MappingConfig  # noqa: E402
from data_pipeline.connectors import NesoDemandConnector  # noqa: E402
from data_pipeline.dashboard_view import (  # noqa: E402
    describe_flag,
    format_age,
    friendly_screening_frame,
)
from data_pipeline.risk_service import assess_snapshot  # noqa: E402
from data_pipeline.snapshot import OperatingSnapshot  # noqa: E402

st.set_page_config(
    page_title="NTRM Resilience Research Demo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px;}
      .hero {padding: 1.6rem 1.8rem; border-radius: 18px;
             background: linear-gradient(120deg, #102a43 0%, #0b7285 100%);
             color: white; margin-bottom: 1rem;}
      .hero h1 {margin: 0 0 .35rem 0; font-size: 2.15rem; color: white;}
      .hero p {margin: 0; color: #e6fcf5; font-size: 1.05rem; max-width: 900px;}
      .step {border: 1px solid rgba(128,128,128,.25); border-radius: 14px;
             padding: 1rem; min-height: 138px;}
      .step-number {font-size: .78rem; font-weight: 700; color: #0b7285;
                    text-transform: uppercase; letter-spacing: .06em;}
      div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.22);
                    border-radius: 14px; padding: .75rem 1rem;}
      .research-note {font-size: .9rem; color: #52616b;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>⚡ Energy-network resilience research demonstrator</h1>
      <p>Explore how a public NESO demand snapshot changes a synthetic IEEE 39-bus
      study, which branch outages cause simulated load loss, and whether constrained
      resources could mitigate the modelled consequence.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.warning(
    "Research prototype dashboard - not validated against AC power flow. "
    "Do not use for operational decisions."
)


@st.cache_resource
def load_case():
    return load_pypower_case("case39")


@st.cache_data(ttl=600, show_spinner=False)
def fetch_live_snapshot() -> OperatingSnapshot:
    return NesoDemandConnector().fetch_latest_actual()


def load_selected_snapshot() -> OperatingSnapshot | None:
    mode = st.sidebar.radio(
        "Data source",
        ("Included example", "Latest valid NESO record", "Upload snapshot JSON"),
        help="The included example is reproducible and works without internet access.",
    )
    if mode == "Included example":
        return OperatingSnapshot.read_json(EXAMPLE_SNAPSHOT)
    if mode == "Latest valid NESO record":
        st.sidebar.caption("NESO settlement data can be delayed and may contain incomplete rows.")
        if st.sidebar.button("Fetch / refresh NESO data", type="primary", use_container_width=True):
            fetch_live_snapshot.clear()
            with st.spinner("Fetching and validating the latest NESO record…"):
                try:
                    st.session_state["live_snapshot"] = fetch_live_snapshot()
                except Exception as exc:
                    st.sidebar.error(f"Could not fetch NESO data: {exc}")
        return cast(OperatingSnapshot | None, st.session_state.get("live_snapshot"))
    uploaded = st.sidebar.file_uploader("Choose a snapshot", type=("json",))
    if uploaded is None:
        return None
    try:
        return OperatingSnapshot.from_dict(json.load(uploaded))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        st.sidebar.error(f"Invalid snapshot: {exc}")
        return None


st.sidebar.header("Study controls")
snapshot = load_selected_snapshot()
case = load_case()
contingency_limit = st.sidebar.slider(
    "N-1 outages to screen",
    1,
    max(len(case.branch_ids), 1),
    min(10, len(case.branch_ids)),
    help="Each scenario removes one branch from the synthetic IEEE network.",
)
include_control = st.sidebar.checkbox(
    "Simulate mitigation for the highest-ranked outage",
    value=True,
)
with st.sidebar.expander("Advanced assumptions"):
    reference_demand = st.number_input(
        "Reference GB demand (MW)", 10_000.0, 60_000.0, 30_000.0, 500.0
    )
    severe_threshold = st.slider("Severe-event threshold (% unserved)", 5, 50, 20, 5) / 100
    use_model = st.checkbox("Use a trained Phase 1 model", value=False)
    model_path_text = st.text_input(
        "Model bundle path",
        str(_ROOT / "cascade_ml" / "models" / "cascade_models.joblib"),
        disabled=not use_model,
    )
    risk_threshold = st.slider(
        "Model threshold for mitigation", 0.05, 0.95, 0.50, 0.05, disabled=not use_model
    )

st.sidebar.divider()
st.sidebar.caption("Tip: you do not need the Deploy button to run this dashboard locally.")

if snapshot is None:
    st.info("Select or fetch a data snapshot in the sidebar to begin.", icon="👈")
    st.stop()
assert snapshot is not None

predictor = None
if use_model:
    model_path = Path(model_path_text)
    if not model_path.exists():
        st.error(
            "The selected model bundle does not exist. Choose another path or disable ML mode."
        )
        st.stop()
    predictor = ModelBundlePredictor(model_path)

contingencies = generate_contingencies(case.branch_ids, max_order=1)[:contingency_limit]
with st.spinner("Running conditional cascade screening…"):
    report = assess_snapshot(
        snapshot,
        case,
        contingencies,
        predictor=predictor,
        mapping_config=MappingConfig(reference_demand_mw=reference_demand),
        include_control=include_control,
        control_risk_threshold=risk_threshold,
        severe_threshold_fraction=severe_threshold,
    )

st.subheader("How to read this dashboard")
step_columns = st.columns(3)
steps = (
    (
        "1 · Public context",
        "A timestamped NESO national-demand record is loaded and quality checked.",
    ),
    ("2 · Synthetic study", "Demand scales an IEEE 39-bus test case within bounded assumptions."),
    (
        "3 · Conditional results",
        "Specified branch outages are simulated; optional resources are tested.",
    ),
)
for column, (number, text) in zip(step_columns, steps, strict=True):
    column.markdown(
        f'<div class="step"><div class="step-number">{number}</div><p>{text}</p></div>',
        unsafe_allow_html=True,
    )

current_age_hours = max(
    (datetime.now(timezone.utc) - snapshot.observed_at).total_seconds() / 3_600,
    0.0,
)
metric_columns = st.columns(4)
metric_columns[0].metric("NESO demand (MW)", f"{snapshot.national_demand_mw:,.0f}")
metric_columns[1].metric("Observation age", format_age(current_age_hours))
metric_columns[2].metric("Synthetic demand scale", f"{report.mapping.applied_demand_scale:.3f}x")
metric_columns[3].metric("Outages screened", len(report.screening))

all_flags = tuple(dict.fromkeys((*snapshot.quality_flags, *report.mapping.warnings)))
if all_flags:
    with st.expander(f"Data and modelling notes ({len(all_flags)})", expanded=True):
        for flag in all_flags:
            st.markdown(f"- **{flag.replace('_', ' ').capitalize()}** — {describe_flag(flag)}")

overview_tab, contingency_tab, intervention_tab, method_tab = st.tabs(
    ("Overview", "Contingency details", "Simulated intervention", "Method & limitations")
)

table = friendly_screening_frame(list(report.screening))
top = report.screening[0]
with overview_tab:
    left, right = st.columns((1, 1.35))
    with left:
        st.markdown("#### Highest-ranked conditional scenario")
        st.metric("Outage branch ID(s)", top.contingency_key)
        st.metric("Simulated unserved load", f"{top.simulated_unserved_mw:,.1f} MW")
        if top.conditional_probability is None:
            st.info(
                "No trained ML model is selected. Ranking uses simulated unserved-load share, "
                "so no probability is being invented."
            )
        else:
            st.metric("Conditional severe-event probability", f"{top.conditional_probability:.1%}")
        st.caption("Branch IDs are zero-based rows in the PYPOWER/MATPOWER case39 branch matrix.")
    with right:
        st.markdown("#### Simulated consequence by outage")
        chart = table.head(12).set_index("Outage branch IDs")[["Simulated unserved load (MW)"]]
        st.bar_chart(chart, color="#0b7285")
        st.caption(
            "Zero means this surrogate produced no final involuntary load loss for that outage."
        )

with contingency_tab:
    st.markdown("#### Ranked conditional screening results")
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Conditional ML probability": st.column_config.ProgressColumn(
                format="percent", min_value=0.0, max_value=1.0
            ),
            "Simulated unserved load (MW)": st.column_config.NumberColumn(format="%.1f"),
            "Unserved share (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )
    st.caption(
        "These are conditional synthetic scenarios—not a forecast that a particular line will fail."
    )

with intervention_tab:
    outcome = report.simulated_intervention
    if not include_control:
        st.info("Mitigation simulation is disabled in the sidebar.")
    elif outcome is None:
        st.success("The selected ML risk gate was not exceeded, so no intervention was activated.")
    elif outcome.action_count == 0:
        st.success(
            "No feasible intervention was required for the highest-ranked screened scenario."
        )
    else:
        st.markdown("#### Before-and-after simulation")
        columns = st.columns(4)
        columns[0].metric("Without control", f"{outcome.baseline_unserved_mw:,.1f} MW")
        columns[1].metric("With control", f"{outcome.controlled_unserved_mw:,.1f} MW")
        columns[2].metric("Preventive curtailment", f"{outcome.preventive_load_shed_mw:,.1f} MW")
        columns[3].metric("Selected actions", outcome.action_count)
        st.info(
            "Preventive curtailment is reported separately from involuntary blackout loss; "
            "it is not counted as a free benefit."
        )
        st.caption(f"Configured intervention cost: {outcome.intervention_cost:,.1f} cost units")

with method_tab:
    st.markdown(
        """
        #### What is calculated

        - NESO demand is converted to a bounded multiplier; it does not provide GB branch flows.
        - The IEEE 39-bus case is solved with a DC power-flow cascade surrogate.
        - Each displayed result is conditional on the listed initiating branch outage.
        - If enabled, resource actions are evaluated by rerunning power flow rather than assuming
          a one-for-one effect on a nearby line.

        #### Important limitations

        - The synthetic mapping is not a regional or national network model.
        - DC power flow omits reactive power, voltage collapse, losses, and detailed protection.
        - AC-CFM comparison is still required before treating surrogate results as validated.
        - Public settlement data may be delayed; the timestamp and quality notes remain visible.
        - Cost units and synthetic resources are experiment parameters, not market recommendations.
        """
    )

st.divider()
st.markdown(
    '<p class="research-note">NTRM research extension · Reproducible synthetic analysis · '
    "No operational recommendation is produced by this interface.</p>",
    unsafe_allow_html=True,
)
