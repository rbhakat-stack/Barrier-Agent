import json
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Barrier-to-Action Agent", layout="wide")

# imports that might use streamlit should come AFTER set_page_config
from claude_client import analyze_barrier
from formatter import normalize_analysis, build_formatted_outputs

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>

/* ── Page padding & background ── */
.main .block-container {
    max-width: 1200px;
    padding: 2rem 3rem 4rem 3rem;
}

/* ── All labels: dark, clean ── */
label, .stTextInput label, .stTextArea label,
div[data-testid="stTextInput"] label,
div[data-testid="stTextAreaRootElement"] label {
    color: #374151 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em;
    margin-bottom: 4px !important;
}

/* ── Text inputs ── */
.stTextInput > div > div > input {
    background-color: #FFFFFF !important;
    border: 1.5px solid #D1D5DB !important;
    border-radius: 8px !important;
    color: #111827 !important;
    font-size: 0.88rem !important;
    padding: 0.55rem 0.85rem !important;
    height: 42px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

.stTextInput > div > div > input:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
    outline: none !important;
}

/* ── Text areas ── */
.stTextArea > div > div > textarea {
    background-color: #FFFFFF !important;
    border: 1.5px solid #D1D5DB !important;
    border-radius: 8px !important;
    color: #111827 !important;
    font-size: 0.88rem !important;
    padding: 0.6rem 0.85rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    resize: vertical;
}

.stTextArea > div > div > textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
    outline: none !important;
}

/* ── Demo scenario buttons ── */
.stButton > button {
    background-color: #F8FAFC !important;
    color: #1E3A5F !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 20px !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    height: 36px !important;
    padding: 0 1rem !important;
    white-space: nowrap !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}

.stButton > button:hover {
    background-color: #1E3A5F !important;
    color: #FFFFFF !important;
    border-color: #1E3A5F !important;
    box-shadow: 0 2px 6px rgba(30, 58, 95, 0.25) !important;
}

/* ── Primary submit button ── */
.stFormSubmitButton > button {
    background-color: #1E3A5F !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    height: 48px !important;
    letter-spacing: 0.03em !important;
    box-shadow: 0 2px 8px rgba(30, 58, 95, 0.25) !important;
    transition: background-color 0.18s ease, box-shadow 0.18s ease !important;
}

.stFormSubmitButton > button:hover {
    background-color: #2563EB !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3) !important;
}

/* ── Form card ── */
[data-testid="stForm"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 14px !important;
    padding: 2rem 2.25rem !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background-color: #1E3A5F !important;
    border-radius: 12px !important;
    padding: 1.1rem 1.4rem !important;
    box-shadow: 0 3px 10px rgba(30, 58, 95, 0.2) !important;
    border: none !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetricLabel"] {
    color: #93C5FD !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}

/* ── Bordered output containers ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    padding: 0.25rem !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
}

/* ── Alert boxes ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.88rem !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}

[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #1E3A5F !important;
    font-size: 0.88rem !important;
    padding: 0.75rem 1rem !important;
}

/* ── Divider ── */
hr {
    border-color: #E5E7EB !important;
    margin: 1.5rem 0 !important;
}

/* ── Code block ── */
code, .stCode {
    border-radius: 8px !important;
    font-size: 0.84rem !important;
}

/* ── Caption / footer ── */
[data-testid="stCaptionContainer"] p {
    color: #9CA3AF !important;
    font-size: 0.78rem !important;
    text-align: center;
}

/* ── Headings ── */
h3, h4 {
    color: #111827;
    font-weight: 700;
    letter-spacing: -0.01em;
}

/* ── Demo pill container label ── */
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
    display: block;
}

/* ── Demo button section wrapper ── */
.demo-section {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 1.25rem 1.5rem 1rem 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

# ── Header banner ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="
    background: linear-gradient(135deg, #0F2A4A 0%, #1E3A5F 45%, #2563EB 100%);
    padding: 2.25rem 2.75rem;
    border-radius: 16px;
    margin-bottom: 1.75rem;
    box-shadow: 0 6px 24px rgba(15, 42, 74, 0.22);
">
    <div style="
        font-size: 0.68rem;
        font-weight: 800;
        color: #60A5FA;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        margin-bottom: 0.6rem;
    ">Pharma Commercial Operations</div>
    <div style="
        color: #FFFFFF;
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        line-height: 1.15;
        margin-bottom: 0.65rem;
    ">Barrier-to-Action Agent</div>
    <div style="
        color: #BFDBFE;
        font-size: 0.9rem;
        line-height: 1.6;
        max-width: 640px;
    ">
        Converts real-world pharma signals into barrier classifications,
        owner assignments, and role-based actions — ready for CRM and field use.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Agent overview ────────────────────────────────────────────────────────────
with st.expander("What this agent does", expanded=False):
    st.markdown("""
    This agent processes structured commercial signals from field teams, hub operations,
    and patient support systems — and returns:

    - **Barrier Classification** — the single most likely barrier blocking therapy progress
    - **Owner Assignment** — the role accountable for resolving it
    - **Recommended Actions** — specific, executable steps mapped to real-world pharma workflows
    - **Formatted Outputs** — CRM-ready task title, owner action card, escalation note, and executive summary

    _Powered by Claude. Designed for pharma commercial operations teams._
    """)

st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

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
st.markdown("""
<div class="demo-section">
    <span class="section-label">Load a Demo Scenario</span>
</div>
""", unsafe_allow_html=True)

# Render buttons inside the visual card using negative margin trick
st.markdown("<div style='margin-top:-3.6rem; padding: 0 1.5rem 1rem 1.5rem;'>", unsafe_allow_html=True)

selected_demo = None
scenario_labels = list(DEMO_SCENARIOS.keys())
row1_labels, row2_labels = scenario_labels[:5], scenario_labels[5:]

row1_cols = st.columns(5)
for col, label in zip(row1_cols, row1_labels):
    if col.button(label, use_container_width=True):
        selected_demo = label

st.markdown("<div style='margin-top:0.4rem;'></div>", unsafe_allow_html=True)

row2_cols = st.columns(5)
for col, label in zip(row2_cols, row2_labels):
    if col.button(label, use_container_width=True):
        selected_demo = label

st.markdown("</div>", unsafe_allow_html=True)

active = DEMO_SCENARIOS[selected_demo] if selected_demo else (
    st.session_state.get("last_input") or list(DEMO_SCENARIOS.values())[0]
)

st.markdown("<div style='margin-top:0.75rem;'></div>", unsafe_allow_html=True)

# ── Input form ────────────────────────────────────────────────────────────────
with st.form("barrier_form"):
    st.markdown("#### Case Signal Input")
    st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="large")

    with col1:
        event_type     = st.text_input("Event Type",     value=active["event_type"])
        patient_status = st.text_area("Patient Status",  value=active["patient_status"],  height=88)
        hcp_activity   = st.text_area("HCP Activity",    value=active["hcp_activity"],    height=88)
        payer_context  = st.text_area("Payer Context",   value=active["payer_context"],   height=88)

    with col2:
        hub_activity   = st.text_area("Hub Activity",    value=active["hub_activity"],    height=88)
        financial_info = st.text_input("Financial Info", value=active["financial_info"])
        timing         = st.text_input("Timing",         value=active["timing"])
        notes          = st.text_area("Notes",           value=active["notes"],           height=88)

    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
    submitted = st.form_submit_button("Analyze Case", use_container_width=True, type="primary")

# ── Analysis ──────────────────────────────────────────────────────────────────
if submitted:
    case_data = {
        "event_type":     event_type,
        "patient_status": patient_status,
        "hcp_activity":   hcp_activity,
        "payer_context":  payer_context,
        "hub_activity":   hub_activity,
        "financial_info": financial_info,
        "timing":         timing,
        "notes":          notes,
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
                    "input":      case_data,
                    "output":     result,
                    "normalized": normalized,
                    "formatted":  formatted,
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

    # KPI row
    st.markdown("### Classification Result")
    st.markdown("<div style='margin-top:0.75rem;'></div>", unsafe_allow_html=True)
    kpi1, kpi2, kpi3 = st.columns(3, gap="medium")
    kpi1.metric("Barrier Detected",  n["barrier"])
    kpi2.metric("Assigned Owner",    n["owner"])
    kpi3.metric("Actions Generated", len(n["actions"]))

    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    st.info(f"**Why:** {n['reason']}")
    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

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
    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
    out_col1, out_col2 = st.columns(2, gap="medium")

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
    st.markdown("<div style='margin-top:0.4rem;'></div>", unsafe_allow_html=True)
    wf_col1, wf_col2, wf_col3, wf_col4 = st.columns(4, gap="small")
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
