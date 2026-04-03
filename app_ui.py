import json
import streamlit as st
from pathlib import Path
from claude_client import analyze_barrier
from formatter import build_formatted_outputs, normalize_analysis

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Barrier-to-Action Agent", layout="wide")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Barrier-to-Action Agent")
st.caption(
    "Converts real-world pharma signals into barrier classifications, "
    "owner assignments, and role-based actions — ready for CRM and field use."
)
st.divider()

# ── Agent overview ────────────────────────────────────────────────────────────
with st.expander("What this agent does", expanded=False):
    st.markdown(
        """
        This agent processes structured commercial signals from field teams, hub operations,
        and patient support systems — and returns:

        - **Barrier Classification** — the single most likely barrier blocking therapy progress
        - **Owner Assignment** — the role accountable for resolving it
        - **Recommended Actions** — specific, executable steps mapped to real-world pharma workflows
        - **Formatted Outputs** — CRM-ready task title, owner action card, escalation note, and executive summary

        _Powered by Claude. Designed for pharma commercial operations teams._
        """
    )

st.markdown("")

# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ── Demo scenario presets — loaded from scenarios.json ────────────────────────
SCENARIO_LABELS = {
    "S1":  "Prior Auth Stall",
    "S2":  "High Copay Drop-off",
    "S3":  "Low Rx Trend",
    "S4":  "Therapy Drop",
    "S5":  "SP Backlog",
    "S6":  "No Hub Referral",
    "S7":  "HCP Query",
    "S8":  "Refill Gap",
    "S9":  "Step Therapy Block",
    "S10": "High Intent Signal",
}

_raw_scenarios = json.loads(Path("scenarios.json").read_text())
DEMO_SCENARIOS = {
    SCENARIO_LABELS[s["id"]]: {k: v for k, v in s.items() if k != "id"}
    for s in _raw_scenarios
    if s["id"] in SCENARIO_LABELS
}

# ── Demo loader ───────────────────────────────────────────────────────────────
st.markdown("**Load a Demo Scenario**")
selected_demo = None
scenario_labels = list(DEMO_SCENARIOS.keys())
row1_labels, row2_labels = scenario_labels[:5], scenario_labels[5:]

row1_cols = st.columns(5)
for col, label in zip(row1_cols, row1_labels):
    if col.button(label, use_container_width=True):
        selected_demo = label

row2_cols = st.columns(5)
for col, label in zip(row2_cols, row2_labels):
    if col.button(label, use_container_width=True):
        selected_demo = label

active = DEMO_SCENARIOS[selected_demo] if selected_demo else (
    st.session_state.get("last_input") or list(DEMO_SCENARIOS.values())[0]
)

st.markdown("")  # spacing

# ── Input form ────────────────────────────────────────────────────────────────
with st.form("barrier_form"):
    st.markdown("#### Case Signal Input")
    col1, col2 = st.columns(2)

    with col1:
        event_type     = st.text_input("Event Type",     value=active["event_type"])
        patient_status = st.text_area("Patient Status",  value=active["patient_status"],  height=80)
        hcp_activity   = st.text_area("HCP Activity",    value=active["hcp_activity"],    height=80)
        payer_context  = st.text_area("Payer Context",   value=active["payer_context"],   height=80)

    with col2:
        hub_activity   = st.text_area("Hub Activity",    value=active["hub_activity"],    height=80)
        financial_info = st.text_input("Financial Info", value=active["financial_info"])
        timing         = st.text_input("Timing",         value=active["timing"])
        notes          = st.text_area("Notes",           value=active["notes"],           height=80)

    submitted = st.form_submit_button("Analyze Case", use_container_width=True, type="primary")

# ── Analysis ──────────────────────────────────────────────────────────────────
if submitted:
    case_data = {
        "event_type": event_type,
        "patient_status": patient_status,
        "hcp_activity": hcp_activity,
        "payer_context": payer_context,
        "hub_activity": hub_activity,
        "financial_info": financial_info,
        "timing": timing,
        "notes": notes,
    }
    st.session_state["last_input"] = case_data

    with st.spinner("Classifying barrier..."):
        try:
            result     = analyze_barrier(case_data)
            normalized = normalize_analysis(result)
            formatted  = build_formatted_outputs(result)
            st.session_state.history.insert(
                0,
                {
                    "input": case_data,
                    "output": result,
                    "normalized": normalized,
                    "formatted": formatted,
                },
            )
        except Exception as e:
            st.error(f"Analysis failed: {e}")

# ── Output ────────────────────────────────────────────────────────────────────
if st.session_state.history:
    latest = st.session_state.history[0]
    n      = latest["normalized"]
    f      = latest["formatted"]

    st.divider()

    # Decision card
    st.markdown("### Classification Result")

    # KPI row
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Barrier Detected",  n["barrier"])
    kpi2.metric("Assigned Owner",    n["owner"])
    kpi3.metric("Actions Generated", len(n["actions"]))

    st.markdown("")
    st.info(f"**Why:** {n['reason']}")
    st.markdown("")

    # Actions
    st.markdown("#### Recommended Actions")
    if n["actions"]:
        for i, action in enumerate(n["actions"], 1):
            st.markdown(f"{i}. {action}")
    else:
        st.caption("No actions generated.")

    st.divider()

    # Formatted outputs
    st.markdown("### Formatted Outputs")
    out_col1, out_col2 = st.columns(2)

    with out_col1:
        with st.container(border=True):
            st.markdown("**CRM Task Title**")
            st.code(f["crm_task_title"], language=None)

        with st.container(border=True):
            st.markdown("**Owner Action Card**")
            st.text(f["owner_action_card"])

    with out_col2:
        with st.container(border=True):
            st.markdown("**Leadership Escalation Note**")
            st.warning(f["leadership_escalation_note"], icon="⚠️")

        with st.container(border=True):
            st.markdown("**Executive Summary**")
            st.success(f["executive_summary"], icon="✅")

    st.divider()

    # Workflow trigger status
    st.markdown("### Workflow Trigger Status")
    wf_col1, wf_col2, wf_col3, wf_col4 = st.columns(4)
    wf_col1.markdown("🟢 **Barrier Classified**")
    wf_col2.markdown("🟢 **Owner Assigned**")
    wf_col3.markdown("🟡 **CRM Task Ready**")
    wf_col4.markdown("🔵 **Escalation Note Generated**")

    st.divider()

    # Raw JSON — collapsed by default
    with st.expander("Raw JSON", expanded=False):
        st.json({"analysis": n, "formatted": f}, expanded=2)

    with st.expander("Input Scenario", expanded=False):
        st.json(latest["input"], expanded=2)

    # History — only shown after more than one run
    if len(st.session_state.history) > 1:
        st.divider()
        st.markdown("### Run History")
        for i, item in enumerate(st.session_state.history[:5], 1):
            label = (
                f"Run {i} — {item['normalized']['barrier']} "
                f"| Owner: {item['normalized']['owner']}"
            )
            with st.expander(label, expanded=False):
                st.json(
                    {"analysis": item["normalized"], "formatted": item["formatted"]},
                    expanded=1,
                )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Demo prototype for Barrier-to-Action workflow orchestration.")
