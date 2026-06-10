from __future__ import annotations

import pytest
from prometheus_client import REGISTRY

from backend.src.observability import ai_metrics
from backend.src.observability.health import healthz
from backend.src.observability.tracing import init_tracer


@pytest.mark.observability
@pytest.mark.unit
def test_health_check_contract():
    assert healthz() == {"status": "ok"}


@pytest.mark.observability
@pytest.mark.unit
def test_ai_metrics_recording_exposes_prometheus_collectors(tenant_id):
    ai_metrics.record_agent_run("lesson_planning", "gpt-4o-mini", str(tenant_id), "completed", 0.25, 1.5, tokens=100)
    ai_metrics.record_tool_execution("student_search", "student_risk", True, 0.01)
    ai_metrics.record_output_review("lesson_planning", "approved", str(tenant_id))

    metric_names = {metric.name for metric in REGISTRY.collect()}
    assert "teacheros_ai_run" in metric_names
    assert "teacheros_ai_cost_cents" in metric_names
    assert "teacheros_ai_tool_execution" in metric_names


@pytest.mark.observability
@pytest.mark.unit
def test_tracing_initializer_is_safe_to_call():
    assert init_tracer() is None


@pytest.mark.observability
@pytest.mark.xfail_architecture_gap(reason="OpenTelemetry trace exporters and HTTP metrics endpoint are not fully wired in create_app yet.")
def test_http_metrics_and_opentelemetry_traces_are_emitted_for_requests():
    assert False, "Requires instrumented FastAPI app with trace exporter and /metrics route."
