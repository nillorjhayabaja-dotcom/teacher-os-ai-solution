"""AI-specific Prometheus metrics for observability."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# --- Run Metrics ---
AI_RUN_DURATION = Histogram(
    "teacheros_ai_run_duration_seconds",
    "AI agent run duration",
    ["agent_kind", "model", "tenant_id"],
    buckets=(1, 2, 5, 10, 30, 60, 120),
)

AI_RUN_TOTAL = Counter(
    "teacheros_ai_run_total",
    "Total AI runs",
    ["agent_kind", "status", "tenant_id"],
)

AI_RUN_ERRORS = Counter(
    "teacheros_ai_run_errors_total",
    "AI run errors",
    ["agent_kind", "error_type", "tenant_id"],
)

# --- Token Metrics ---
AI_TOKENS_TOTAL = Counter(
    "teacheros_ai_tokens_total",
    "Total tokens consumed",
    ["model", "token_type", "tenant_id"],
)

# --- Cost Metrics ---
AI_COST_TOTAL = Counter(
    "teacheros_ai_cost_cents_total",
    "Total AI cost in cents",
    ["agent_kind", "model", "tenant_id"],
)

AI_BUDGET_USAGE = Gauge(
    "teacheros_ai_budget_usage_pct",
    "Budget usage percentage per tenant",
    ["tenant_id", "period"],
)

# --- Quality Metrics ---
AI_OUTPUT_REVIEW = Counter(
    "teacheros_ai_output_review_total",
    "AI output review outcomes",
    ["agent_kind", "review_state", "tenant_id"],
)

AI_FEEDBACK_RATING = Histogram(
    "teacheros_ai_feedback_rating",
    "AI output feedback ratings",
    ["agent_kind"],
    buckets=(1, 2, 3, 4, 5),
)

# --- RAG Metrics ---
AI_RAG_SEARCH_DURATION = Histogram(
    "teacheros_ai_rag_search_duration_seconds",
    "RAG vector search duration",
    ["tenant_id"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
)

AI_RAG_CHUNKS_RETRIEVED = Histogram(
    "teacheros_ai_rag_chunks_retrieved",
    "Number of RAG chunks retrieved per query",
    ["tenant_id"],
    buckets=(0, 1, 3, 5, 10, 20),
)

# --- Tool Metrics ---
AI_TOOL_EXECUTION = Counter(
    "teacheros_ai_tool_execution_total",
    "Tool executions by agents",
    ["tool_name", "success", "agent_kind"],
)

AI_TOOL_DURATION = Histogram(
    "teacheros_ai_tool_duration_seconds",
    "Tool execution duration",
    ["tool_name"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)


def record_agent_run(agent_kind: str, model: str, tenant_id: str, status: str, latency_s: float, cost_cents: float, tokens: int = 0):
    """Record metrics for a completed agent run."""
    AI_RUN_TOTAL.labels(agent_kind=agent_kind, status=status, tenant_id=tenant_id).inc()
    AI_RUN_DURATION.labels(agent_kind=agent_kind, model=model, tenant_id=tenant_id).observe(latency_s)
    if cost_cents > 0:
        AI_COST_TOTAL.labels(agent_kind=agent_kind, model=model, tenant_id=tenant_id).inc(cost_cents)
    if tokens > 0:
        AI_TOKENS_TOTAL.labels(model=model, token_type="total", tenant_id=tenant_id).inc(tokens)


def record_tool_execution(tool_name: str, agent_kind: str, success: bool, duration_s: float):
    """Record metrics for a tool execution."""
    AI_TOOL_EXECUTION.labels(tool_name=tool_name, success=str(success).lower(), agent_kind=agent_kind).inc()
    AI_TOOL_DURATION.labels(tool_name=tool_name).observe(duration_s)


def record_output_review(agent_kind: str, review_state: str, tenant_id: str):
    """Record metrics for an output review."""
    AI_OUTPUT_REVIEW.labels(agent_kind=agent_kind, review_state=review_state, tenant_id=tenant_id).inc()