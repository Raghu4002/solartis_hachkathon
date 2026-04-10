# Solartis AI Query Analyzer

**Submitted for:** Solartis AI Engineering Internship – 3 Day Challenge


---

## Problem Understanding

Database engineers working on insurance policy administration systems often face slow queries, anomalies and performance issues that are hard to diagnose quickly. The problem is not just detecting that a query is slow — it is understanding why it is slow and what exactly needs to be fixed.

This system takes a natural language query like "Why is pagination slow?" or "Is this an anomaly?", finds the most relevant performance cases from a knowledge base using RAG, and returns a structured response with the problem, root cause, fix suggestion and severity — all without needing a live database connection.

---

## Architecture

The system has two pipelines:

**Data Ingestion Pipeline**

`dataset.py` generates 60 structured performance cases → saved as `dataset.json` → `upsert_to_pinecone.py` builds rich text from each case and uploads to Pinecone index (`solartis-rag`) using the `llama-text-embed-v2` integrated embedding model (768 dimensions).

**Live Query Pipeline**

User enters a question in the Streamlit UI → `retrieve()` sends the query to Pinecone which embeds it and returns the top 3 semantically matching cases → the matched cases plus the original query are passed to Groq API (llama-3.3-70b-versatile) via `analyze()` which builds a structured prompt → Groq returns a structured JSON response → Streamlit renders metric cards, severity badge, diagnosis and fix example.

**Development version (app1.py)** replaces Pinecone with local keyword matching and replaces Groq with mock API functions — no external keys needed, works fully offline.

---

## How to Run

**Step 1 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 2 — Run without API keys (development)**
```bash
streamlit run app1.py
```
Opens at: http://localhost:8501

**Step 3 — Run with real Pinecone + Groq (production version)**

Create a `.env` file:
```
PINECONE_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

Upload dataset to Pinecone:
```bash
python upsert_to_pinecone.py
```

Run:
```bash
streamlit run app.py
```

**Try these queries:**
- `Why is my query taking 2469 seconds?`
- `How to fix slow JSON field filtering?`
- `Is 50 second latency spike an anomaly?`
- `Pagination slow after page 1000`

---

## Project Files

```
app1.py                 — Development version (mock APIs)
mock_api.py             — Three API functions: analyze, detect_anomaly, suggest_optimization
dataset.json            — 60 database performance scenarios across 8 categories
dataset.py              — Script that generates dataset.json
upsert_to_pinecone.py   — Uploads dataset to Pinecone with integrated embedding
requirements.txt        — All dependencies
.env                    — API keys 
```

---

## Design Decisions

**60 cases instead of the minimum 3**
The challenge asked for at least 3 cases. I built 60 across 8 categories — full table scans, JSON filtering, complex joins, high frequency queries, pagination issues, anomalies, write performance and schema design. A broader knowledge base means the system handles more variations of the same question rather than failing on slight rephrasing.

**Pinecone with integrated embedding instead of local sentence-transformers**
I used Pinecone's `llama-text-embed-v2` model which embeds the text on Pinecone's side. This removes the dependency on a local embedding model, makes the retrieval semantically much stronger than keyword matching, and reduces setup complexity since no sentence-transformers download is needed for the production version.

**Mock APIs for development (app1.py)**
The three mock functions in `mock_api.py` implement deterministic rule-based logic for analyzing, detecting anomalies and suggesting fixes. This means the development version works without any API keys, produces reproducible results and is easy to understand and test. The same interface is used in both versions so switching from mock to real is just changing the import.

**Groq (llama-3.3-70b) for generation**
The production version passes retrieved context plus the user query to Groq. The LLM's job is only to reason over the retrieved cases and format the response — not to recall facts from training. This keeps hallucination low because the answer is grounded in the matched cases.

**Streamlit for UI**
Streamlit gave a complete working UI with expandable sections, metric cards and JSON display in about 300 lines. For a 3-day challenge the goal was a working demo, not a production frontend.

---

## Trade-offs

| Decision | What was chosen | What was given up |
|---|---|---|
| Dataset size | 60 hand-crafted cases | Real query logs from an actual database |
| Retrieval (dev) | Keyword matching | Semantic accuracy (~70% vs ~95%) |
| Retrieval (prod) | Pinecone semantic search | Self-hosted vector DB control |
| LLM | Groq free tier | Dedicated deployment with SLA |
| UI | Streamlit | Scalable frontend for multiple users |
| APIs | Mock deterministic functions | Real EXPLAIN ANALYZE on live queries |

---

## If I Were Designing This for Production at Scale

The current system is a working prototype. Moving it to production for a real insurance platform would require changes at every layer.

**Data layer** — Instead of 60 hand-crafted cases, the knowledge base would be built from millions of real slow query logs ingested automatically from the database's slow query log. A pipeline would continuously extract new slow queries, generate embeddings and upsert them to Pinecone so the system gets smarter over time without manual updates.

**Retrieval layer** — The current Pinecone semantic search is already close to production quality. The improvement would be fine-tuning the embedding model on insurance-specific SQL patterns so that domain-specific terms like `policy_data`, `claims_data` and `premium_amount` are understood more precisely.

**LLM layer** — The Groq free tier would be replaced with a dedicated LLM deployment with an SLA. For cost efficiency, a smaller fine-tuned model specialised on SQL analysis could replace a general 70B model for most queries, with fallback to a larger model for complex cases.

**API layer** — The mock functions would be replaced with real implementations. `analyze_query` would run `EXPLAIN ANALYZE` on the actual query against the live database. `detect_anomaly` would compare against a historical baseline using statistical thresholds rather than fixed rules. `suggest_optimization` would check existing indexes before recommending new ones.

**Infrastructure** — The Streamlit single-user app would be replaced with a React frontend and FastAPI backend, deployed on Kubernetes with auto-scaling. A Redis cache would store results for repeated queries reducing LLM calls significantly.

**Monitoring** — The production system would need full observability — Prometheus and Grafana for metrics, alerts for new anomaly patterns, and a feedback loop where DBAs can mark suggestions as helpful or not to improve retrieval ranking over time.

The core RAG and API architecture would stay the same. The change is replacing mock components with real ones and adding the infrastructure around them.

---

## AI Usage Disclosure

| Tool | Used for | Contribution |
|---|---|---|
| GitHub Copilot | Code completions, variable names | ~15% |
| Claude | Dataset case ideation, architecture design | ~20% |
| Manual work | RAG logic, mock API rules, Pinecone integration, Streamlit UI, prompt design | ~65% |

Copilot completions were accepted roughly 40% of the time and modified or rejected the rest. Claude suggestions were used as reference and reimplemented from scratch. The keyword matching algorithm, anomaly detection rules, category-based optimization mapping and Pinecone integrated embedding setup were all built manually.

**Challenges faced:**
- Pinecone `.search()` threw an AttributeError — resolved by switching to `upsert_records` with integrated embedding and `query_records` interface
- LLM hallucination risk on edge case queries — mitigated by grounding the prompt strictly in retrieved cases and keeping temperature low
- Dataset was initially too small — expanded from the 3 example cases to 60 comprehensive cases across 8 categories

---

**Status:** End-to-end working system, ready for evaluation.


Production level architecture (at rough sketch):

Current working system: 