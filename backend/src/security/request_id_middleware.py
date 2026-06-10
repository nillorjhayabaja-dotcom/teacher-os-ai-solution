"""Request ID and correlation ID middleware.

Generates unique request IDs and propagates correlation IDs for:
- Request tracing across microservices
- Audit trail correlation
- Log aggregation
- Distributed tracing
"""

from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.src.core.constants import (
    HEADER_REQUEST_ID,
    HEADER_CORRELATION_ID,
    HEADER_FORWARDED_FOR,
    HEADER_REAL_IP,
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique request ID to every request.

    If the client sends a ``X-Request-Id`` header, it is preserved.
    Otherwise, a new UUID is generated.
    
    Also extracts and propagates:
    - ``X-Correlation-Id`` for distributed tracing
    - Client IP from ``X-Forwarded-For`` or ``X-Real-IP``
    - ``User-Agent`` for audit logging
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or preserve request ID
        request_id = request.headers.get(HEADER_REQUEST_ID, str(uuid.uuid4()))
        request.state.request_id = request_id

        # Propagate or generate correlation ID
        correlation_id = request.headers.get(
            HEADER_CORRELATION_ID, str(uuid.uuid4())
        )
        request.state.correlation_id = correlation_id

        # Extract client IP
        forwarded_for = request.headers.get(HEADER_FORWARDED_FOR, "")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.headers.get(HEADER_REAL_IP, request.client.host if request.client else "unknown")
        request.state.client_ip = client_ip

        # Extract user agent
        user_agent = request.headers.get("User-Agent", "")
        request.state.user_agent = user_agent

        # Process the request
        response = await call_next(request)

        # Add request ID headers to response
        response.headers[HEADER_REQUEST_ID] = request_id
        response.headers[HEADER_CORRELATION_ID] = correlation_id

        return response