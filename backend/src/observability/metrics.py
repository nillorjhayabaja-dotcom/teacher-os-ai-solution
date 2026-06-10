from __future__ import annotations

"""Prometheus metrics scaffold.

Foundational platform placeholder.
"""

from prometheus_client import Counter, Histogram, start_http_server

from backend.src.core.settings import settings


REQUEST_LATENCY = Histogram(
    "teacheros_api_request_latency_seconds", "API request latency", buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10)
)

REQUEST_ERRORS = Counter(
    "teacheros_api_request_errors_total", "API request errors", ["status_code"]
)


def start_metrics_server() -> None:  # pragma: no cover
    start_http_server(int(settings.PROMETHEUS_METRICS_PORT))

