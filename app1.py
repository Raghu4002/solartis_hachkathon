import streamlit as st
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

# ── Mock APIs (the 3 endpoints from the challenge doc) ─────────────────────────
from mock_api import analyze_query, detect_anomaly, suggest_optimization, run_full_pipeline

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Query Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
.stApp { background: linear-gradient(135deg, #F8FAFB 0%, #FFFFFF 100%); color: #1F2937; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2.5rem 3.5rem 4rem; max-width: 1200px; }

.hero-wrap { background: linear-gradient(135deg, #FFFFFF 0%, #F3F4F6 100%); border-bottom: 2px solid #E5E7EB; border-radius: 16px; padding: 2.5rem; margin-bottom: 2.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.hero-tag { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: .14em; color: #3B82F6; text-transform: uppercase; margin-bottom: 12px; font-weight: 600; }
.hero-title { font-size: 38px; font-weight: 700; color: #111827; margin: 0 0 8px; letter-spacing: -.5px; line-height: 1.2; }
.hero-sub { font-size: 15px; color: #6B7280; margin: 0; line-height: 1.5; }

.stTextArea textarea { background: #FFFFFF !important; border: 2px solid #E5E7EB !important; border-radius: 12px !important; color: #111827 !important; font-family: 'DM Sans', sans-serif !important; font-size: 15px !important; padding: 14px 16px !important; transition: all .25s ease !important; }
.stTextArea textarea:focus { border-color: #3B82F6 !important; box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1) !important; }

.stButton > button { background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important; color: #fff !important; border: none !important; border-radius: 10px !important; padding: 12px 32px !important; font-family: 'Inter', sans-serif !important; font-size: 15px !important; font-weight: 600 !important; cursor: pointer !important; transition: all .2s ease !important; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important; }
.stButton > button:hover { background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important; transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important; }

.metric-row { display: flex; gap: 16px; margin: 2rem 0 2.5rem; }
.metric-card { flex: 1; background: linear-gradient(135deg, #FFFFFF 0%, #F9FAFB 100%); border: 2px solid #E5E7EB; border-radius: 14px; padding: 22px 24px; text-align: center; transition: all .2s ease; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.metric-card:hover { border-color: #3B82F6; box-shadow: 0 4px 16px rgba(59, 130, 246, 0.1); }
.metric-val { font-size: 32px; font-weight: 700; color: #1F2937; font-family: 'JetBrains Mono', monospace; }
.metric-lbl { font-size: 13px; color: #6B7280; margin-top: 8px; letter-spacing: .04em; font-weight: 500; }

.result-card { background: linear-gradient(135deg, #FFFFFF 0%, #F9FAFB 100%); border: 2px solid #E5E7EB; border-radius: 12px; padding: 18px 22px; margin-bottom: 14px; transition: all .2s ease; }
.result-card:hover { border-color: #3B82F6; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08); }
.result-label { font-size: 11px; font-weight: 700; color: #3B82F6; text-transform: uppercase; letter-spacing: .12em; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace; }
.result-value { font-size: 15px; color: #1F2937; line-height: 1.6; font-weight: 500; }
.result-value code { background: #F3F4F6; color: #2563EB; padding: 2px 8px; border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; border: 1px solid #E5E7EB; }

.badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; font-family: 'JetBrains Mono', monospace; letter-spacing: .04em; }
.badge-critical { background: #FEE2E2; color: #DC2626; border: 1.5px solid #FCA5A5; }
.badge-high     { background: #FEF3C7; color: #D97706; border: 1.5px solid #FCD34D; }
.badge-medium   { background: #DBEAFE; color: #2563EB; border: 1.5px solid #93C5FD; }
.badge-low      { background: #DCFCE7; color: #16A34A; border: 1.5px solid #86EFAC; }
.badge-conf     { background: #ECFDF5; color: #059669; border: 1.5px solid #A7F3D0; }

.json-wrap { background: #F9FAFB; border: 2px solid #E5E7EB; border-radius: 12px; padding: 16px 20px; margin-top: 8px; }
.json-wrap pre { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #2563EB; margin: 0; white-space: pre-wrap; line-height: 1.7; }
.section-divider { border: none; border-top: 2px solid #E5E7EB; margin: 2.5rem 0; }
.chip-label { font-size: 11px; color: #3B82F6; text-transform: uppercase; letter-spacing: .12em; font-family: 'JetBrains Mono', monospace; margin-bottom: 12px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ── Example queries ────────────────────────────────────────────────────────────
EXAMPLE_QUERIES = [
    "Why is my query taking 2469 seconds?",
    "How to fix slow JSON field filtering?",
    "Is 50 second latency spike an anomaly?",
    "My config query is fast but DB is overloaded",
    "Why is COUNT query with joins so slow?",
    "Pagination slow after page 1000",
]


# ══════════════════════════════════════════════════════════════════════════════
# Mock RAG — Simple keyword matching on dataset.json
# ══════════════════════════════════════════════════════════════════════════════


def retrieve(user_query: str) -> list[dict]:
    """
    Mock retrieval: Search dataset.json for cases matching user query keywords.
    Returns top 3 most relevant cases.
    """
    import json
    with open("dataset.json", "r") as f:
        dataset = json.load(f)
    
    user_words = set(word.lower() for word in user_query.split() if len(word) > 2)
    matches = []
    
    for case in dataset:
        keywords = set(kw.lower() for kw in case.get("keywords", []))
        case_name_lower = case.get("case_name", "").lower()
        problem_lower = case.get("problem", "").lower()
        
        # Check for keyword overlap or direct matches in case name/problem
        if (user_words & keywords) or any(word in case_name_lower or word in problem_lower for word in user_words):
            matches.append(case)
    
    # Return top 3 matches (simple: just the first 3 found)
    return matches[:3]


# ══════════════════════════════════════════════════════════════════════════════
# LLM — Groq (Llama-3)
# ══════════════════════════════════════════════════════════════════════════════
def analyze(user_query: str, cases: list[dict]) -> dict:
    """
    Mock analysis: Use the mock API to analyze the query.
    """
    return analyze_query(user_query, cases)


# ── UI Helpers ─────────────────────────────────────────────────────────────────
def badge_html(label, kind):
    return f'<span class="badge badge-{kind}">{label}</span>'

def metric_row(cases_matched, response_time, confidence):
    return f"""
    <div class="metric-row">
        <div class="metric-card"><div class="metric-val">{cases_matched}</div><div class="metric-lbl">Cases matched</div></div>
        <div class="metric-card"><div class="metric-val">{response_time}</div><div class="metric-lbl">Response time</div></div>
        <div class="metric-card"><div class="metric-val">{confidence.capitalize()}</div><div class="metric-lbl">Confidence</div></div>
    </div>"""

def result_card(label, value):
    return f"""<div class="result-card"><div class="result-label">{label}</div><div class="result-value">{value}</div></div>"""


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="chip-label">Try an example</div>', unsafe_allow_html=True)
    for eq in EXAMPLE_QUERIES:
        if st.button(eq, key=f"ex_{eq[:20]}"):
            st.session_state["prefill"] = eq
            st.rerun()
    st.markdown("---")
    st.markdown('<div class="chip-label">Stack</div>', unsafe_allow_html=True)
    st.markdown("🔍 **RAG:** Mock keyword search on dataset.json")
    st.markdown("🤖 **LLM:** Mock analysis APIs")
    st.markdown("🖥️ **UI:** Streamlit")


# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-tag">⚡ Solartis AI Internship Challenge</div>
    <div class="hero-title">AI Query Analyzer</div>
    <div class="hero-sub">Groq LLM + Pinecone RAG (llama-text-embed-v2) — ask anything about slow queries or anomalies</div>
</div>
""", unsafe_allow_html=True)


# ── Input ──────────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", "")
user_query = st.text_area(
    label="Your question",
    value=prefill,
    placeholder="e.g. Why is my query taking 2469 seconds to run?",
    height=90,
    label_visibility="collapsed",
)

col1, col2 = st.columns([1, 5])
with col1:
    analyze_clicked = st.button("⚡ Analyze", use_container_width=True)


# ── Analysis ───────────────────────────────────────────────────────────────────
if analyze_clicked and user_query.strip():
    t0 = time.time()

    with st.spinner("Searching Pinecone knowledge base..."):
        retrieved = retrieve(user_query)

    if not retrieved:
        st.warning("No matching cases found. Try rephrasing your question.")
        st.stop()

    with st.spinner("Analyzing with Groq LLM..."):
        try:
            result = analyze(user_query, retrieved)
        except json.JSONDecodeError:
            st.error("LLM returned invalid JSON. Please try again.")
            st.stop()

    elapsed = round(time.time() - t0, 2)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        metric_row(len(retrieved), f"{elapsed}s", result.get("confidence", "medium")),
        unsafe_allow_html=True,
    )

    # ── Run all 3 mock APIs ────────────────────────────────────────────────
    pipeline = run_full_pipeline(user_query, retrieved)
    summary  = pipeline["summary"]
    api1     = pipeline["step_1_analyze"]
    api2     = pipeline["step_2_anomaly"]
    api3     = pipeline["step_3_optimize"]

    left, right = st.columns([3, 2])

    with left:
        st.markdown(result_card("Matched case", f"<strong>{summary.get('matched_case','—')}</strong>"), unsafe_allow_html=True)
        st.markdown(result_card("Problem", summary.get("problem", "—")), unsafe_allow_html=True)
        st.markdown(result_card("Root cause", summary.get("root_cause", "—")), unsafe_allow_html=True)
        st.markdown(result_card("Suggestion", summary.get("suggestion", "—")), unsafe_allow_html=True)
        if summary.get("fix_example"):
            st.markdown(result_card("Fix example", f"<code>{summary['fix_example']}</code>"), unsafe_allow_html=True)

        sev  = summary.get("severity", "medium")
        conf = summary.get("confidence", "medium")
        anom = summary.get("is_anomaly", False)
        st.markdown(f"""
        <div style="display:flex;gap:20px;margin-top:4px;">
            <div><div class="result-label" style="margin-bottom:6px;">Severity</div>{badge_html(sev.upper(), sev)}</div>
            <div><div class="result-label" style="margin-bottom:6px;">Confidence</div>{badge_html(conf.upper(), "conf")}</div>
            <div><div class="result-label" style="margin-bottom:6px;">Anomaly?</div>{badge_html("YES" if anom else "NO", "critical" if anom else "conf")}</div>
        </div>""", unsafe_allow_html=True)

        # Priority steps from API 3
        steps = summary.get("priority_steps", [])
        if steps:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Priority steps")
            for i, step in enumerate(steps, 1):
                st.markdown(f"`{i}.` {step}")

    with right:
        # ── Show each API response separately ─────────────────────────────
        st.markdown("#### API responses")

        with st.expander("GET /analyze/query", expanded=True):
            st.markdown(f"""
            <div class="result-label">Category</div>
            <div class="result-value" style="margin-bottom:8px;"><code>{api1.get('category','')}</code></div>
            <div class="result-label">Detected patterns</div>
            """, unsafe_allow_html=True)
            for p in api1.get("detected_patterns", []):
                st.markdown(f"- {p}")
            st.markdown(f'<div class="json-wrap"><pre>{json.dumps({"problem": api1.get("problem"), "root_cause": api1.get("root_cause"), "severity": api1.get("severity")}, indent=2)}</pre></div>', unsafe_allow_html=True)

        with st.expander("POST /detect/anomaly"):
            is_anom = api2.get("is_anomaly", False)
            color = "#E24B4A" if is_anom else "#1D9E75"
            st.markdown(f'<div style="font-size:20px;font-weight:500;color:{color};margin-bottom:8px;">{"ANOMALY DETECTED" if is_anom else "No anomaly"}</div>', unsafe_allow_html=True)
            for r in api2.get("reasons", []):
                st.markdown(f"- {r}")
            st.markdown(f'<div class="json-wrap"><pre>{json.dumps({"is_anomaly": api2.get("is_anomaly"), "anomaly_type": api2.get("anomaly_type"), "recommended_action": api2.get("recommended_action")}, indent=2)}</pre></div>', unsafe_allow_html=True)

        with st.expander("GET /suggest/optimization"):
            st.markdown(f"**Estimated improvement:** {api3.get('estimated_improvement','')}")
            st.markdown(f'<div class="json-wrap"><pre>{json.dumps({"suggestion": api3.get("suggestion"), "fix_example": api3.get("fix_example"), "confidence": api3.get("confidence")}, indent=2)}</pre></div>', unsafe_allow_html=True)

        # Top matched cases from Pinecone
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Top matched cases")
        for i, c in enumerate(retrieved):
            name = c.get("case_name", f"Case {i+1}")
            with st.expander(f"{i+1}. {name}"):
                st.markdown(f"**Category:** `{c.get('category','')}`")
                st.markdown(f"**Execution time:** `{c.get('execution_time_sec','')}s`")
                st.markdown(f"**Frequency:** `{c.get('frequency','')}`")
                st.markdown(f"**Context:** {c.get('root_cause','')}")
                if c.get("query"):
                    st.code(c["query"], language="sql")

elif analyze_clicked and not user_query.strip():
    st.warning("Please enter a question before clicking Analyze.")

else:
    st.markdown("""
    <div style="text-align:center;padding:4rem 0;color:#3A4060;">
        <div style="font-size:36px;margin-bottom:12px;">⚡</div>
        <div style="font-size:15px;font-family:'JetBrains Mono',monospace;">
            Type a question above or pick an example from the sidebar
        </div>
    </div>
    """, unsafe_allow_html=True)