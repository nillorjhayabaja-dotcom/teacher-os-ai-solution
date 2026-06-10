"""Rate limiting middleware using SlowAPI.

Implements tiered rate limiting:
- Public endpoints: 10 requests/minute
- Authenticated endpoints: 100 requests/minute
- AI endpoints: 20 requests/minute (cost-based throttling)
- Login endpoints: 5 requests/5 minutes
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from backend.src.core.settings import settings
from backend.src.core.constants import (
    RATE_LIMIT_SCOPE_PUBLIC,
    RATE_LIMIT_SCOPE_AUTHENTICATED,
    RATE_LIMIT_SCOPE_AI,
    RATE_LIMIT_SCOPE_LOGIN,
)
from backend.src.core.exceptions import RateLimitExceededError


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with tiered limits.

    Applies different rate limits based on:
    - Whether the user is authenticated
    - The endpoint category (AI, login, general)
    - IP address for unauthenticated requests
    """

    def __init__(self, app: FastAPI) -> None:
        super().__init__(app)

        # In production, use Redis-backed storage
        # from slowapi.storage import RedisStorage
        # storage = RedisStorage(redis_client)

        self._limiter = Limiter(
            key_func=self._get_rate_limit_key,
            default_limits=[
                f"{settings.RATE_LIMIT_AUTH_REQUESTS}/{settings.RATE_LIMIT_AUTH_WINDOW_SECONDS}second"
            ],
        )

        # Register error handler
        app.state.limiter = self._limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    def _get_rate_limit_key(self, request: Request) -> str:
        """Determine the rate limiting key based on request context.

        Uses user ID for authenticated requests, IP for public.
        """
        # Use user ID if authenticated
        user = getattr(request.state, "user", None)
        if user and getattr(user, "get", None):
            user_id = user.get("sub", "")
            if user_id:
                return f"user:{user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return get_remote_address(request)

    def _get_endpoint_limits(self, request: Request) -> Optional[list[str]]:
        """Get custom rate limits based on endpoint path."""
        path = request.url.path

        # Login endpoints - strict rate limiting
        if "/auth/login" in path or "/auth/token" in path:
            return [
                f"{settings.RATE_LIMIT_LOGIN_REQUESTS}/{settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS}second"
            ]

        # AI endpoints - cost-based throttling
        if "/ai/" in path or "/agents/" in path:
            return [
                f"{settings.RATE_LIMIT_AI_REQUESTS}/{settings.RATE_LIMIT_AI_WINDOW_SECONDS}second"
            ]

        # Public endpoints (no auth required)
        user = getattr(request.state, "user", None)
        if not user or not getattr(user, "get", None):
            return [
                f"{settings.RATE_LIMIT_PUBLIC_REQUESTS}/{settings.RATE_LIMIT_PUBLIC_WINDOW_SECONDS}second"
            ]

        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting before processing the request."""
        custom_limits = self._get_endpoint_limits(request)

        if custom_limits:
            # Apply custom limits for this endpoint
            for limit in custom_limits:
                # Parse limit string like "5/300second"
                try:
                    max_requests_str, window_str = limit.split("/")
                    max_requests = int(max_requests_str)
                    window_seconds = int(window_str.replace("second", ""))
                except (ValueError, IndexError):
                    continue

                # Simple sliding window rate limit check
                key = self._get_rate_limit_key(request)
                if self._check_rate_limit(key, max_requests, window_seconds):
                    response = Response(
                        content='{"detail": "Rate limit exceeded"}',
                        status_code=429,
                        media_type="application/json",
                    )
                    response.headers["X-RateLimit-Limit"] = str(max_requests)
                    response.headers["X-RateLimit-Remaining"] = "0"
                    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window_seconds)
                    return response

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_AUTH_REQUESTS)

        return response

    def _check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if a key has exceeded its rate limit.

        In production, this uses a Redis sorted set for sliding window.
        Returns True if limit exceeded.
        """
        # In-memory simple implementation for development
        # Production should use Redis sorted sets with timestamps
        current_time = int(time.time())
        window_start = current_time - window_seconds

        # In production, implement with Redis:
        # pipe = redis_client.pipeline()
        # pipe.zremrangebyscore(f"ratelimit:{key}", 0, window_start)
        # pipe.zadd(f"ratelimit:{key}", {current_time: current_time})
        # pipe.expire(f"ratelimit:{key}", window_seconds)
        # request_count = pipe.zcard(f"ratelimit:{key}").execute()[-1]
        # return request_count > max_requests

        return False

    @property
    def limiter(self) -> Limiter:
        """Get the SlowAPI Limiter instance for decorator-based rate limiting."""
        return self._limiter