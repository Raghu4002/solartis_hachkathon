"""
mock_api.py
───────────
The 3 mock APIs from the Solartis challenge document.
These simulate real API endpoints using your dataset.

Usage in app.py:
    from mock_api import analyze_query, detect_anomaly, suggest_optimization
"""

import json


# ── Load dataset once at module level ─────────────────────────────────────────
with open("dataset.json") as f:
    DATASET = json.load(f)


# ══════════════════════════════════════════════════════════════════════════════
# API 1 — GET /analyze/query
# Input : a SQL query string
# Output: problem type, category, root cause, execution time
# ══════════════════════════════════════════════════════════════════════════════
def analyze_query(sql_query: str, retrieved_cases: list[dict]) -> dict:
    """
    Simulates: GET /analyze/query

    Takes the user's SQL query + RAG-retrieved cases.
    Returns what kind of problem it is and why.

    In production this would:
    - Connect to real DB and run EXPLAIN on the query
    - Pull actual execution stats from slow_query_log
    - Return real metrics
    """
    if not retrieved_cases:
        return {
            "status": "error",
            "message": "No matching cases found in knowledge base"
        }

    top = retrieved_cases[0]

    # Detect query patterns from the SQL itself
    sql_upper = sql_query.upper().strip()
    detected_patterns = []

    if "SELECT *" in sql_upper:
        detected_patterns.append("SELECT * — fetches all columns unnecessarily")
    if "WHERE" not in sql_upper and any(k in sql_upper for k in ["SELECT", "UPDATE", "DELETE"]):
        detected_patterns.append("No WHERE clause — full table operation")
    if "JOIN" in sql_upper and sql_upper.count("JOIN") >= 2:
        detected_patterns.append("Multiple JOINs detected")
    if "JSON_EXTRACT" in sql_upper or "JSON_TABLE" in sql_upper:
        detected_patterns.append("JSON operation in WHERE — index likely not used")
    if "LIKE '%" in sql_upper:
        detected_patterns.append("Leading wildcard LIKE — index disabled")
    if "OFFSET" in sql_upper:
        detected_patterns.append("Large OFFSET pagination — scans and discards rows")
    if "ORDER BY" in sql_upper and "LIMIT" not in sql_upper:
        detected_patterns.append("ORDER BY without LIMIT — sorts entire result set")
    if "IN (SELECT" in sql_upper:
        detected_patterns.append("Subquery in IN clause — may run per outer row")
    if "YEAR(" in sql_upper or "MONTH(" in sql_upper or "DATE(" in sql_upper:
        detected_patterns.append("Function on column in WHERE — index disabled")

    return {
        "api": "GET /analyze/query",
        "status": "success",
        "matched_case": top.get("case_name", "Unknown"),
        "category": top.get("category", "unknown"),
        "problem": top.get("problem", ""),
        "root_cause": top.get("root_cause", ""),
        "execution_time_sec": top.get("execution_time_sec", "unknown"),
        "frequency": top.get("frequency", "unknown"),
        "detected_patterns": detected_patterns if detected_patterns else ["No obvious anti-patterns detected in query syntax"],
        "severity": top.get("severity", "medium"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# API 2 — POST /detect/anomaly
# Input : execution_time_sec, frequency, category from matched case
# Output: is_anomaly (bool), reason, anomaly_type
# ══════════════════════════════════════════════════════════════════════════════
def detect_anomaly(retrieved_cases: list[dict]) -> dict:
    """
    Simulates: POST /detect/anomaly

    Looks at execution time and frequency to decide if behavior is abnormal.

    Anomaly rules:
    - Execution time > 30 sec            → time anomaly
    - Frequency > 10000/hour             → frequency anomaly
    - Category is explicitly 'anomaly'   → known anomaly pattern
    - Sudden spike (in case name)        → spike anomaly

    In production this would:
    - Compare against historical baseline for that specific query
    - Use statistical thresholds (e.g. 3x standard deviation)
    - Pull real-time metrics from monitoring system
    """
    if not retrieved_cases:
        return {"status": "error", "message": "No cases to analyze"}

    top = retrieved_cases[0]

    try:
        exec_time = float(top.get("execution_time_sec", 0))
    except (ValueError, TypeError):
        exec_time = 0

    frequency  = str(top.get("frequency", "")).lower()
    category   = top.get("category", "")
    case_name  = top.get("case_name", "").lower()

    is_anomaly   = False
    anomaly_type = "none"
    reasons      = []

    # Rule 1 — execution time threshold
    if exec_time > 60:
        is_anomaly = True
        anomaly_type = "execution_time"
        reasons.append(f"Execution time {exec_time}s exceeds critical threshold of 60s")
    elif exec_time > 30:
        is_anomaly = True
        anomaly_type = "execution_time"
        reasons.append(f"Execution time {exec_time}s exceeds warning threshold of 30s")

    # Rule 2 — frequency overload
    freq_num = 0
    for part in frequency.replace("/", " ").split():
        if part.isdigit():
            freq_num = int(part)
            break
    if freq_num > 10000:
        is_anomaly = True
        anomaly_type = "frequency_overload"
        reasons.append(f"Query called {frequency} — connection pool at risk")

    # Rule 3 — known anomaly category
    if category == "anomaly":
        is_anomaly = True
        anomaly_type = "known_anomaly_pattern"
        reasons.append("Matches a known production anomaly pattern in knowledge base")

    # Rule 4 — spike pattern in case name
    if "spike" in case_name or "sudden" in case_name or "deadlock" in case_name:
        is_anomaly = True
        anomaly_type = "sudden_spike"
        reasons.append("Pattern matches sudden performance degradation / spike scenario")

    return {
        "api": "POST /detect/anomaly",
        "status": "success",
        "is_anomaly": is_anomaly,
        "anomaly_type": anomaly_type,
        "confidence": "high" if len(reasons) >= 2 else "medium" if reasons else "low",
        "reasons": reasons if reasons else ["No anomaly detected — query behavior appears normal"],
        "execution_time_sec": exec_time,
        "frequency": top.get("frequency", "unknown"),
        "recommended_action": (
            "URGENT: Investigate immediately" if exec_time > 100 or freq_num > 50000
            else "WARNING: Monitor closely" if is_anomaly
            else "OK: No immediate action needed"
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# API 3 — GET /suggest/optimization
# Input : matched case from RAG
# Output: suggestion, fix_example, estimated_improvement
# ══════════════════════════════════════════════════════════════════════════════
def suggest_optimization(retrieved_cases: list[dict]) -> dict:
    """
    Simulates: GET /suggest/optimization

    Returns specific, actionable fix recommendations with SQL examples.

    In production this would:
    - Run EXPLAIN ANALYZE on the actual query
    - Check existing indexes on the table
    - Generate index suggestions based on real schema
    - Estimate query improvement after fix
    """
    if not retrieved_cases:
        return {"status": "error", "message": "No cases to optimize"}

    top = retrieved_cases[0]
    category = top.get("category", "")

    # Estimate improvement based on category
    improvement_map = {
        "full_table_scan":   "80–99% reduction in execution time after adding WHERE + index",
        "index_issue":       "60–90% faster after adding correct index",
        "join_performance":  "50–80% faster after indexing join columns",
        "anomaly":           "Depends on root cause — investigate locks/stats first",
        "frequency":         "90–99% DB load reduction after adding Redis cache",
        "schema_design":     "Long-term: prevents table from growing unmanageable",
        "write_performance": "40–70% faster writes after batching and indexing",
        "system_config":     "System-wide improvement for all queries",
    }

    # Priority steps based on category
    priority_map = {
        "full_table_scan":   ["Add WHERE clause immediately", "Add index on filter columns", "Use LIMIT for exploratory queries"],
        "index_issue":       ["Run EXPLAIN to confirm index is missing", "Add the suggested index", "Verify with EXPLAIN after"],
        "join_performance":  ["Index all JOIN columns", "Filter before joining", "Consider rewriting with CTE"],
        "anomaly":           ["Run SHOW PROCESSLIST", "Check for table locks", "Run ANALYZE TABLE to refresh stats"],
        "frequency":         ["Add Redis cache with 5-min TTL", "Load static data at app startup", "Batch similar queries"],
        "schema_design":     ["Add the suggested column/index", "Migrate data if needed", "Update queries to use new structure"],
        "write_performance": ["Add index on filter column", "Process in batches of 10k", "Schedule during off-peak hours"],
        "system_config":     ["Apply config change", "Monitor with SHOW STATUS", "Verify improvement in slow query log"],
    }

    return {
        "api": "GET /suggest/optimization",
        "status": "success",
        "matched_case": top.get("case_name", ""),
        "suggestion": top.get("suggestion", ""),
        "fix_example": top.get("fix_example", ""),
        "priority_steps": priority_map.get(category, ["Review the suggestion and apply the fix example"]),
        "estimated_improvement": improvement_map.get(category, "Significant improvement expected"),
        "confidence": top.get("confidence", "medium"),
        "severity": top.get("severity", "medium"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Combined pipeline — calls all 3 APIs in sequence
# This is what the Agent would do automatically
# ══════════════════════════════════════════════════════════════════════════════
def run_full_pipeline(sql_query: str, retrieved_cases: list[dict]) -> dict:
    """
    Runs all 3 mock APIs in sequence and combines results.
    This is the MCP-style multi-step agent flow.

    Flow:
      1. analyze_query   → what is the problem?
      2. detect_anomaly  → is it an anomaly?
      3. suggest_optimization → how to fix it?
    """
    analysis     = analyze_query(sql_query, retrieved_cases)
    anomaly      = detect_anomaly(retrieved_cases)
    optimization = suggest_optimization(retrieved_cases)

    return {
        "pipeline": "full_analysis",
        "step_1_analyze":  analysis,
        "step_2_anomaly":  anomaly,
        "step_3_optimize": optimization,
        # Quick summary combining all 3
        "summary": {
            "matched_case":    analysis.get("matched_case", ""),
            "problem":         analysis.get("problem", ""),
            "root_cause":      analysis.get("root_cause", ""),
            "is_anomaly":      anomaly.get("is_anomaly", False),
            "anomaly_type":    anomaly.get("anomaly_type", "none"),
            "suggestion":      optimization.get("suggestion", ""),
            "fix_example":     optimization.get("fix_example", ""),
            "priority_steps":  optimization.get("priority_steps", []),
            "improvement":     optimization.get("estimated_improvement", ""),
            "severity":        analysis.get("severity", "medium"),
            "confidence":      optimization.get("confidence", "medium"),
        }
    }