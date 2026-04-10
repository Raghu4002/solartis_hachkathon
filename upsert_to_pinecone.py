"""
upsert_to_pinecone.py  — UPDATED for Integrated Embedding
──────────────────────────────────────────────────────────
Your Pinecone index uses llama-text-embed-v2 (NVIDIA hosted, 768-dim).
Pinecone does the embedding automatically — no local model needed.

Steps:
  1. pip install pinecone-client python-dotenv   (no sentence-transformers needed!)
  2. Create .env with PINECONE_API_KEY=...
  3. python upsert_to_pinecone.py
"""

import json
import os
import time
from dotenv import load_dotenv

load_dotenv()


def build_text(case: dict) -> str:
    """
    Build a rich text string from each case.
    Pinecone's llama-text-embed-v2 will embed this text automatically.
    We combine all fields so ANY kind of user question can match.
    """
    keywords_str = ", ".join(case.get("keywords", []))
    return (
        f"Case: {case['case_name']}. "
        f"Problem: {case['problem']}. "
        f"Root cause: {case['root_cause']}. "
        f"Suggestion: {case['suggestion']}. "
        f"Fix: {case.get('fix_example', '')}. "
        f"Keywords: {keywords_str}. "
        f"Category: {case['category']}. "
        f"Severity: {case['severity']}. "
        f"Query pattern: {case['query']}."
    )


def main():
    # ── Load dataset ──────────────────────────────────────────────────────
    with open("dataset.json") as f:
        dataset = json.load(f)
    print(f"Loaded {len(dataset)} cases from dataset.json\n")

    # ── Connect to Pinecone ───────────────────────────────────────────────
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in .env file!")

    from pinecone import Pinecone
    pc = Pinecone(api_key=api_key)

    # ── Connect to your existing index ────────────────────────────────────
    # IMPORTANT: Change this to match your exact index name in Pinecone dashboard
    index_name = "solartis-rag"   # <-- change to YOUR index name
    index = pc.Index(index_name)

    print(f"Connected to Pinecone index: '{index_name}'")
    print("Using integrated embedding: llama-text-embed-v2 (768-dim)\n")

    # ── Build records for upsert ──────────────────────────────────────────
    # With integrated embedding each record has:
    #   - id     : unique string
    #   - text   : the field Pinecone embeds (matches "Record field" = "text")
    #   - rest   : metadata stored alongside the vector

    print(f"Upserting {len(dataset)} records...\n")

    batch_size = 10
    batch = []

    for i, case in enumerate(dataset):
        record = {
            "id":   case["id"],
            "text": build_text(case),   # Pinecone embeds this automatically

            # Metadata returned in query results
            "case_name":          case["case_name"],
            "query":              case["query"],
            "execution_time_sec": str(case["execution_time_sec"]),
            "frequency":          case["frequency"],
            "category":           case["category"],
            "problem":            case["problem"],
            "root_cause":         case["root_cause"],
            "suggestion":         case["suggestion"],
            "fix_example":        case.get("fix_example", ""),
            "severity":           case["severity"],
            "confidence":         case["confidence"],
            "keywords":           ", ".join(case.get("keywords", [])),
        }
        batch.append(record)
        print(f"  [{i+1:02d}/{len(dataset)}] Prepared: {case['case_name'][:55]}")

        if len(batch) >= batch_size:
            index.upsert_records(namespace="__default__", records=batch)
            print(f"  --> Upserted batch of {len(batch)} records\n")
            batch = []
            time.sleep(1)

    if batch:
        index.upsert_records(namespace="__default__", records=batch)
        print(f"  --> Upserted final batch of {len(batch)} records\n")

    # ── Verify ────────────────────────────────────────────────────────────
    time.sleep(3)
    stats = index.describe_index_stats()
    total = stats.get("total_vector_count", "?")
    print(f"Done! Index '{index_name}' now has {total} vectors.")
    print("\nNext step: run  streamlit run app.py")


if __name__ == "__main__":
    main()