import html
import json
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Barrier-to-Action Agent", layout="wide")

from claude_client import analyze_barrier
from formatter import build_formatted_outputs, normalize_analysis


SCENARIO_LABELS = {
    "S1": "Prior Auth Stall",
    "S2": "High Copay Drop-off",
    "S3": "Low Rx Trend",
    "S4": "Therapy Drop",
    "S5": "SP Backlog",
    "S6": "No Hub Referral",
    "S7": "HCP Query",
    "S8": "Refill Gap",
    "S9": "Step Therapy Block",
    "S10": "High Intent Signal",
}


st.markdown(
    """
    <style>
    :root {
        --ink: #10233f;
        --muted: #5f708a;
        --line: #d7e0ea;
        --panel: rgba(255, 255, 255, 0.92);
        --panel-strong: #ffffff;
        --accent: #0f5bd8;
        --accent-deep: #0b3d91;
        --accent-soft: #e8f0ff;
        --success: #0f7b6c;
        --warning: #c17a10;
        --shadow: 0 20px 50px rgba(11, 36, 71, 0.10);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(15, 91, 216, 0.10), transparent 34%),
            radial-gradient(circle at top right, rgba(16, 35, 63, 0.08), transparent 28%),
            linear-gradient(180deg, #f6f8fb 0%, #eef3f8 100%);
    }

    .main .block-container {
        max-width: 1240px;
        padding-top: 2rem;
        padding-bottom: 3rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    h1, h2, h3, h4, p, li, label {
        color: var(--ink);
    }

    .hero-shell {
        position: relative;
        overflow: hidden;
        background: linear-gradient(140deg, #0f223f 0%, #173c68 55%, #0f5bd8 100%);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 28px;
        padding: 2rem 2.2rem;
        box-shadow: 0 28px 60px rgba(9, 26, 51, 0.22);
        margin-bottom: 1.5rem;
    }

    .hero-shell:before {
        content: "";
        position: absolute;
        inset: auto -10% -35% auto;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.16), transparent 62%);
    }

    .hero-kicker {
        display: inline-block;
        font-size: 0.72rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        font-weight: 700;
        color: #8ec1ff;
        margin-bottom: 0.8rem;
    }

    .hero-title {
        font-size: 2.25rem;
        line-height: 1.05;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #ffffff;
        margin-bottom: 0.85rem;
        max-width: 760px;
    }

    .hero-copy {
        max-width: 720px;
        font-size: 1rem;
        line-height: 1.65;
        color: rgba(235, 243, 255, 0.92);
    }

    .hero-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.85rem;
        margin-top: 1.4rem;
    }

    .hero-chip {
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 18px;
        padding: 0.9rem 1rem;
        backdrop-filter: blur(12px);
    }

    .hero-chip-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #9cc6ff;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }

    .hero-chip-value {
        color: white;
        font-size: 0.95rem;
        font-weight: 600;
        line-height: 1.4;
    }

    .section-card {
        background: var(--panel);
        border: 1px solid rgba(16, 35, 63, 0.08);
        border-radius: 24px;
        padding: 1.4rem;
        box-shadow: var(--shadow);
        backdrop-filter: blur(10px);
        margin-bottom: 1.15rem;
    }

    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }

    .section-copy {
        color: var(--muted);
        font-size: 0.9rem;
        line-height: 1.55;
        margin-bottom: 1rem;
    }

    .stat-card {
        background: linear-gradient(180deg, #ffffff 0%, #f7faff 100%);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1rem 1.1rem;
        min-height: 112px;
        box-shadow: 0 10px 24px rgba(16, 35, 63, 0.06);
    }

    .stat-label {
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--muted);
        margin-bottom: 0.8rem;
    }

    .stat-value {
        font-size: 1.25rem;
        font-weight: 750;
        color: var(--ink);
        line-height: 1.3;
    }

    .insight-band {
        background: linear-gradient(90deg, rgba(15, 91, 216, 0.08), rgba(15, 91, 216, 0.02));
        border: 1px solid rgba(15, 91, 216, 0.14);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        margin-top: 0.9rem;
    }

    .insight-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-weight: 700;
        color: var(--accent-deep);
        margin-bottom: 0.45rem;
    }

    .insight-copy {
        color: var(--ink);
        font-size: 0.96rem;
        line-height: 1.6;
    }

    .action-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1rem 1.1rem;
        box-shadow: 0 12px 28px rgba(16, 35, 63, 0.05);
        margin-bottom: 0.85rem;
    }

    .action-index {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent-deep);
        font-weight: 800;
        font-size: 0.9rem;
        margin-bottom: 0.7rem;
    }

    .action-text {
        color: var(--ink);
        font-size: 0.97rem;
        line-height: 1.6;
        font-weight: 500;
    }

    .output-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 1.1rem 1.15rem;
        min-height: 220px;
        box-shadow: 0 14px 28px rgba(16, 35, 63, 0.06);
    }

    .output-kicker {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: var(--muted);
        margin-bottom: 0.7rem;
    }

    .output-body {
        color: var(--ink);
        white-space: pre-wrap;
        line-height: 1.65;
        font-size: 0.95rem;
    }

    .output-card.crm {
        background: linear-gradient(180deg, #f7fbff 0%, #eef5ff 100%);
    }

    .output-card.escalation {
        background: linear-gradient(180deg, #fffaf0 0%, #fff4dc 100%);
    }

    .output-card.summary {
        background: linear-gradient(180deg, #f4fcf8 0%, #e9f8f0 100%);
    }

    .history-pill {
        display: inline-block;
        padding: 0.32rem 0.7rem;
        border-radius: 999px;
        border: 1px solid rgba(15, 91, 216, 0.16);
        background: rgba(15, 91, 216, 0.06);
        color: var(--accent-deep);
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.8rem;
    }

    .stTextInput label, .stTextArea label {
        color: var(--ink) !important;
        font-weight: 650 !important;
        font-size: 0.83rem !important;
    }

    .stTextInput input, .stTextArea textarea {
        border-radius: 16px !important;
        border: 1px solid #cad5e2 !important;
        background: rgba(255, 255, 255, 0.92) !important;
        color: var(--ink) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75) !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 4px rgba(15, 91, 216, 0.12) !important;
    }

    div[data-testid="stForm"] {
        border: 1px solid rgba(16, 35, 63, 0.08) !important;
        border-radius: 24px !important;
        background: rgba(255, 255, 255, 0.88) !important;
        box-shadow: var(--shadow) !important;
        padding: 1.25rem 1.2rem 1.35rem 1.2rem !important;
    }

    .stFormSubmitButton button {
        border-radius: 16px !important;
        border: none !important;
        background: linear-gradient(135deg, #123461 0%, #0f5bd8 100%) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em !important;
        min-height: 3rem !important;
        box-shadow: 0 16px 32px rgba(15, 91, 216, 0.22) !important;
    }

    .stFormSubmitButton button p,
    .stFormSubmitButton button span,
    .stFormSubmitButton button div {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    .stButton button {
        border-radius: 999px !important;
        border: 1px solid #c7d6eb !important;
        background: rgba(255, 255, 255, 0.88) !important;
        color: var(--ink) !important;
        font-weight: 650 !important;
        min-height: 2.6rem !important;
    }

    .stButton button:hover {
        border-color: var(--accent) !important;
        color: var(--accent-deep) !important;
    }

    div[data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.88) !important;
        border: 1px solid rgba(16, 35, 63, 0.08) !important;
        border-radius: 20px !important;
        overflow: hidden;
    }

    div[data-testid="stExpander"] summary {
        font-weight: 650 !important;
        color: var(--ink) !important;
    }

    @media (max-width: 900px) {
        .hero-grid {
            grid-template-columns: 1fr;
        }

        .hero-title {
            font-size: 1.8rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if "history" not in st.session_state:
    st.session_state.history = []


raw_scenarios = json.loads(Path("scenarios.json").read_text())
demo_scenarios = {
    SCENARIO_LABELS[item["id"]]: {k: v for k, v in item.items() if k != "id"}
    for item in raw_scenarios
    if item["id"] in SCENARIO_LABELS
}

if "form_fields" not in st.session_state:
    st.session_state.form_fields = dict(next(iter(demo_scenarios.values())))


st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Executive Demo Surface</div>
        <div class="hero-title">Barrier-to-Action intelligence for commercial pharma teams</div>
        <div class="hero-copy">
            Turn field, payer, hub, and patient signals into a single barrier diagnosis, a clear accountable owner,
            and ready-to-use operational outputs for CRM, escalation, and leadership review.
        </div>
        <div class="hero-grid">
            <div class="hero-chip">
                <div class="hero-chip-label">Decision</div>
                <div class="hero-chip-value">One barrier prioritized from fragmented commercial signals</div>
            </div>
            <div class="hero-chip">
                <div class="hero-chip-label">Execution</div>
                <div class="hero-chip-value">Role-based actions generated for the field and support teams</div>
            </div>
            <div class="hero-chip">
                <div class="hero-chip-label">Readout</div>
                <div class="hero-chip-value">CRM, escalation, and executive artifacts produced in the same workflow</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.expander("About this demo", expanded=False):
    st.write(
        "This view is designed for leadership demos. It highlights the barrier decision, accountable owner, "
        "recommended actions, and the downstream formatted outputs in a compact executive workflow."
    )


st.markdown(
    """
    <div class="section-card">
        <div class="history-pill">Demo Scenarios</div>
        <div class="section-title">Load a realistic pharma signal</div>
        <div class="section-copy">Use one of the prepared scenarios to move quickly in a live demo, or edit the inputs below before analyzing.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

scenario_labels = list(demo_scenarios.keys())
row_one = st.columns(5)
for col, label in zip(row_one, scenario_labels[:5]):
    if col.button(label, use_container_width=True):
        st.session_state.form_fields = dict(demo_scenarios[label])

row_two = st.columns(5)
for col, label in zip(row_two, scenario_labels[5:10]):
    if col.button(label, use_container_width=True):
        st.session_state.form_fields = dict(demo_scenarios[label])


form_values = st.session_state.form_fields

left_col, right_col = st.columns([1.05, 1.35], gap="large")

with left_col:
    with st.form("barrier_form"):
        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Case Signal Input</div>
                <div class="section-copy">Capture the event, patient context, payer friction, and operational notes that describe the current case state.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button(
            "Analyze Case",
            use_container_width=True,
            type="primary",
        )
        st.markdown("<div style='margin-bottom:0.85rem;'></div>", unsafe_allow_html=True)

        event_type     = st.text_input("Event Type",     value=form_values.get("event_type",     ""))
        patient_status = st.text_area("Patient Status",  value=form_values.get("patient_status", ""), height=96)
        hcp_activity   = st.text_area("HCP Activity",    value=form_values.get("hcp_activity",   ""), height=96)
        payer_context  = st.text_area("Payer Context",   value=form_values.get("payer_context",  ""), height=96)
        hub_activity   = st.text_area("Hub Activity",    value=form_values.get("hub_activity",   ""), height=96)
        financial_info = st.text_input("Financial Info", value=form_values.get("financial_info", ""))
        timing         = st.text_input("Timing",         value=form_values.get("timing",         ""))
        notes          = st.text_area("Notes",           value=form_values.get("notes",          ""), height=96)

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
    st.session_state.form_fields = dict(case_data)

    with st.spinner("Analyzing barrier and generating outputs..."):
        try:
            result = analyze_barrier(case_data)
            normalized = normalize_analysis(result)
            formatted = build_formatted_outputs(result)
            st.session_state.history.insert(
                0,
                {
                    "input": case_data,
                    "output": result,
                    "normalized": normalized,
                    "formatted": formatted,
                },
            )
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")


def render_stat_card(label: str, value: str) -> None:
    safe_label = html.escape(label)
    safe_value = html.escape(value)
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">{safe_label}</div>
            <div class="stat-value">{safe_value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_output_card(title: str, body: str, extra_class: str = "") -> None:
    safe_title = html.escape(title)
    safe_body = html.escape(body)
    st.markdown(
        f"""
        <div class="output-card {extra_class}">
            <div class="output-kicker">{safe_title}</div>
            <div class="output-body">{safe_body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with right_col:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Decision Output</div>
            <div class="section-copy">A polished readout for leadership, sales operations, or cross-functional review.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.history:
        latest = st.session_state.history[0]
        analysis = latest["normalized"]
        formatted = latest["formatted"]

        stat_one, stat_two, stat_three = st.columns(3, gap="small")
        with stat_one:
            render_stat_card("Barrier", analysis["barrier"])
        with stat_two:
            render_stat_card("Owner", analysis["owner"])
        with stat_three:
            render_stat_card("Actions Generated", str(len(analysis["actions"])))

        safe_reason = html.escape(analysis["reason"])
        st.markdown(
            f"""
            <div class="insight-band">
                <div class="insight-label">Why this barrier</div>
                <div class="insight-copy">{safe_reason}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="section-card" style="margin-top: 1rem;">
                <div class="section-title">Recommended Actions</div>
                <div class="section-copy">Clear next steps for the assigned owner and supporting teams.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if analysis["actions"]:
            for idx, action in enumerate(analysis["actions"], start=1):
                safe_action = html.escape(action)
                st.markdown(
                    f"""
                    <div class="action-card">
                        <div class="action-index">{idx}</div>
                        <div class="action-text">{safe_action}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No actions were returned for this case.")

        st.markdown(
            """
            <div class="section-card" style="margin-top: 1rem;">
                <div class="section-title">Formatted Outputs</div>
                <div class="section-copy">These artifacts are ready to copy into downstream workflows, leadership updates, and CRM tasks.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        output_left, output_right = st.columns(2, gap="medium")
        with output_left:
            render_output_card("CRM Task Title", formatted["crm_task_title"], "crm")
            st.markdown("<div style='height:0.9rem;'></div>", unsafe_allow_html=True)
            render_output_card("Owner Action Card", formatted["owner_action_card"])
        with output_right:
            render_output_card("Leadership Escalation Note", formatted["leadership_escalation_note"], "escalation")
            st.markdown("<div style='height:0.9rem;'></div>", unsafe_allow_html=True)
            render_output_card("Executive Summary", formatted["executive_summary"], "summary")

        with st.expander("Raw JSON", expanded=False):
            st.json({"analysis": analysis, "formatted": formatted}, expanded=2)

        with st.expander("Input Scenario", expanded=False):
            st.json(latest["input"], expanded=2)
    else:
        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Ready for demo</div>
                <div class="section-copy">Choose a prepared scenario or enter a case signal on the left, then run the analysis to populate the executive view.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

if len(st.session_state.history) > 1:
    st.markdown(
        """
        <div class="section-card" style="margin-top: 0.8rem;">
            <div class="section-title">Session History</div>
            <div class="section-copy">Recent analyses from the current demo session.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for idx, item in enumerate(st.session_state.history[:5], start=1):
        label = f"Run {idx} | {item['normalized']['barrier']} | Owner: {item['normalized']['owner']}"
        with st.expander(label, expanded=False):
            st.json({"analysis": item["normalized"], "formatted": item["formatted"]}, expanded=1)

st.caption("Barrier-to-Action Agent demo surface for commercial leadership review.")
