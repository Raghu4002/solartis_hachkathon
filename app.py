import streamlit as st
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

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
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0D0F14; color: #E8E6DF; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem; max-width: 1100px; }

.hero-wrap { border-bottom: 1px solid #1E2130; padding-bottom: 2rem; margin-bottom: 2.5rem; }
.hero-tag { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: .14em; color: #4A7CF7; text-transform: uppercase; margin-bottom: 10px; }
.hero-title { font-size: 34px; font-weight: 600; color: #F2F0E8; margin: 0 0 6px; letter-spacing: -.5px; line-height: 1.2; }
.hero-sub { font-size: 14px; color: #5A5F72; margin: 0; }

.stTextArea textarea { background: #13161F !important; border: 1px solid #1E2130 !important; border-radius: 10px !important; color: #E8E6DF !important; font-family: 'DM Sans', sans-serif !important; font-size: 15px !important; padding: 14px 16px !important; transition: border-color .2s; }
.stTextArea textarea:focus { border-color: #4A7CF7 !important; box-shadow: 0 0 0 3px rgba(74,124,247,.12) !important; }

.stButton > button { background: #4A7CF7 !important; color: #fff !important; border: none !important; border-radius: 8px !important; padding: 10px 28px !important; font-family: 'DM Sans', sans-serif !important; font-size: 14px !important; font-weight: 500 !important; cursor: pointer !important; transition: background .18s, transform .1s !important; }
.stButton > button:hover { background: #3A6AE0 !important; transform: translateY(-1px) !important; }

.metric-row { display: flex; gap: 14px; margin: 1.8rem 0 2rem; }
.metric-card { flex: 1; background: #13161F; border: 1px solid #1E2130; border-radius: 10px; padding: 18px 20px; text-align: center; }
.metric-val { font-size: 26px; font-weight: 600; color: #F2F0E8; font-family: 'JetBrains Mono', monospace; }
.metric-lbl { font-size: 12px; color: #5A5F72; margin-top: 4px; letter-spacing: .04em; }

.result-card { background: #13161F; border: 1px solid #1E2130; border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; }
.result-label { font-size: 10px; font-weight: 600; color: #3A4060; text-transform: uppercase; letter-spacing: .1em; margin-bottom: 6px; font-family: 'JetBrains Mono', monospace; }
.result-value { font-size: 14px; color: #C8C6BE; line-height: 1.6; }
.result-value code { background: #1A1E2B; color: #4A7CF7; padding: 1px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 12px; }

.badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; font-family: 'JetBrains Mono', monospace; letter-spacing: .04em; }
.badge-critical { background: rgba(226,75,74,.15); color: #E24B4A; border: 1px solid rgba(226,75,74,.3); }
.badge-high     { background: rgba(239,159,39,.15); color: #EF9F27; border: 1px solid rgba(239,159,39,.3); }
.badge-medium   { background: rgba(74,124,247,.15); color: #4A7CF7; border: 1px solid rgba(74,124,247,.3); }
.badge-low      { background: rgba(29,158,117,.15); color: #1D9E75; border: 1px solid rgba(29,158,117,.3); }
.badge-conf     { background: rgba(29,158,117,.12); color: #1D9E75; border: 1px solid rgba(29,158,117,.25); }

.json-wrap { background: #0A0C12; border: 1px solid #1E2130; border-radius: 10px; padding: 16px 20px; margin-top: 6px; }
.json-wrap pre { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #5A8F6A; margin: 0; white-space: pre-wrap; line-height: 1.7; }
.section-divider { border: none; border-top: 1px solid #1E2130; margin: 2rem 0; }
.chip-label { font-size: 11px; color: #3A4060; text-transform: uppercase; letter-spacing: .1em; font-family: 'JetBrains Mono', monospace; margin-bottom: 10px; }
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
# RAG — Pinecone Integrated Embedding (llama-text-embed-v2)
# No sentence-transformers needed! Pinecone embeds the query automatically.
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_pinecone_index():
    from pinecone import Pinecone
    api_key = st.secrets.get("PINECONE_API_KEY") or os.getenv("PINECONE_API_KEY")
    if not api_key:
        st.error("PINECONE_API_KEY not found. Add it to .streamlit/secrets.toml")
        st.stop()
    pc = Pinecone(api_key=api_key)
    index_name = "solartis-rag"   # <-- must match your Pinecone index name
    return pc.Index(index_name)


def retrieve(user_query: str) -> list[dict]:
    """
    Search Pinecone using integrated embedding.
    Pinecone converts the query text to a 768-dim vector internally.
    Returns top 3 most similar cases as metadata dicts.
    """
    index = get_pinecone_index()
    results = index.search(
        namespace="__default__",
        query={
            "inputs": {"text": user_query},   # Pinecone embeds this for you
            "top_k": 3,
        },
        fields=["case_name", "query", "execution_time_sec", "frequency",
                "category", "problem", "root_cause", "suggestion",
                "fix_example", "severity", "confidence", "keywords"],
    )
    # Extract metadata from each hit
    hits = results.get("result", {}).get("hits", [])
    return [hit.get("fields", {}) for hit in hits]


# ══════════════════════════════════════════════════════════════════════════════
# LLM — Groq (Llama-3)
# ══════════════════════════════════════════════════════════════════════════════
def analyze(user_query: str, cases: list[dict]) -> dict:
    """
    Send user query + retrieved cases to Groq LLM.
    Returns structured JSON with problem, root_cause, suggestion, severity, confidence.
    """
    from groq import Groq

    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY not found. Add it to .streamlit/secrets.toml")
        st.stop()

    client = Groq(api_key=api_key)
    context_str = json.dumps(cases, indent=2)

    prompt = f"""You are a database performance expert for an insurance policy system.

User question: {user_query}

Here are the most relevant cases from the knowledge base:
{context_str}

Based on the above cases, analyze the user's question and return ONLY a valid JSON object.
No markdown, no backticks, no explanation — just the raw JSON.

JSON must have exactly these keys:
{{
  "matched_case": "name of the most relevant case",
  "problem": "one sentence describing the problem",
  "root_cause": "detailed explanation of why this happens",
  "suggestion": "specific actionable steps to fix this",
  "fix_example": "a SQL or code example of the fix",
  "severity": "one of: critical, high, medium, low",
  "confidence": "one of: high, medium, low"
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=800,
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown backticks if model adds them
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


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
    st.markdown("🔍 **RAG:** Pinecone `llama-text-embed-v2`")
    st.markdown("🤖 **LLM:** Groq `llama3-8b-8192`")
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

    left, right = st.columns([3, 2])

    with left:
        st.markdown(result_card("Matched case", f"<strong>{result.get('matched_case','—')}</strong>"), unsafe_allow_html=True)
        st.markdown(result_card("Problem", result.get("problem", "—")), unsafe_allow_html=True)
        st.markdown(result_card("Root cause", result.get("root_cause", "—")), unsafe_allow_html=True)
        st.markdown(result_card("Suggestion", result.get("suggestion", "—")), unsafe_allow_html=True)

        if result.get("fix_example"):
            st.markdown(result_card("Fix example", f"<code>{result['fix_example']}</code>"), unsafe_allow_html=True)

        sev  = result.get("severity", "medium")
        conf = result.get("confidence", "medium")
        st.markdown(f"""
        <div style="display:flex;gap:20px;margin-top:4px;">
            <div><div class="result-label" style="margin-bottom:6px;">Severity</div>{badge_html(sev.upper(), sev)}</div>
            <div><div class="result-label" style="margin-bottom:6px;">Confidence</div>{badge_html(conf.upper(), "conf")}</div>
        </div>""", unsafe_allow_html=True)

    with right:
        st.markdown("#### Raw JSON")
        out = {k: v for k, v in result.items()}
        st.markdown(f'<div class="json-wrap"><pre>{json.dumps(out, indent=2)}</pre></div>', unsafe_allow_html=True)

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