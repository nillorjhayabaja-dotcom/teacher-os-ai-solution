"""CSRF protection middleware for sensitive POST requests.

Implements double-submit cookie pattern:
- Generates a CSRF token on the first visit
- Validates the token on sensitive POST/PUT/DELETE requests
- Uses SameSite cookies and secure flags
"""

from __future__ import annotations

import secrets
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.src.core.settings import settings
from backend.src.core.constants import HEADER_CSRF_TOKEN

# Methods that require CSRF protection
CSRF_PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths exempt from CSRF protection
CSRF_EXEMPT_PATHS = {
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware using double-submit cookie pattern.

    For each session, a CSRF token is set as a cookie. Protected requests
    must include this token in the X-CSRF-Token header. The server validates
    that the header value matches the cookie value.

    In production, use SameSite=Strict cookies with the Secure flag.
    """

    def __init__(self, app, *, exempt_paths: Optional[set] = None) -> None:
        super().__init__(app)
        self._exempt_paths = exempt_paths or CSRF_EXEMPT_PATHS
        self._cookie_name = "csrf_token"
        self._header_name = HEADER_CSRF_TOKEN

    def _generate_token(self) -> str:
        """Generate a cryptographically secure CSRF token."""
        return secrets.token_urlsafe(32)

    def _is_exempt(self, request: Request) -> bool:
        """Check if the request path is exempt from CSRF protection."""
        path = request.url.path
        for exempt_path in self._exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate CSRF token on protected requests."""
        # Skip CSRF for exempt paths
        if self._is_exempt(request):
            response = await call_next(request)
            return response

        # For non-protected methods, just set the cookie on the response
        if request.method not in CSRF_PROTECTED_METHODS:
            response = await call_next(request)
            self._set_csrf_cookie(response)
            return response

        # Validate CSRF token for protected methods
        cookie_token = request.cookies.get(self._cookie_name)
        header_token = request.headers.get(self._header_name)

        if not cookie_token or not header_token:
            return Response(
                content='{"detail": "CSRF token missing"}',
                status_code=403,
                media_type="application/json",
            )

        if not secrets.compare_digest(cookie_token, header_token):
            return Response(
                content='{"detail": "CSRF token mismatch"}',
                status_code=403,
                media_type="application/json",
            )

        response = await call_next(request)
        # Rotate CSRF token after successful validation
        self._set_csrf_cookie(response)
        return response

    def _set_csrf_cookie(self, response: Response) -> None:
        """Set or refresh the CSRF cookie on the response.
        
        SECURITY NOTE: httponly MUST be False for the double-submit cookie pattern
        because JavaScript needs to read the cookie value and send it as a header.
        SameSite=Strict provides the CSRF protection; httponly is for XSS cookie theft.
        """
        token = self._generate_token()
        response.set_cookie(
            key=self._cookie_name,
            value=token,
            max_age=3600,  # 1 hour
            httponly=False,  # Must be readable by JS for double-submit pattern
            samesite="strict",
            secure=settings.ENVIRONMENT != "development",
            path="/",
        )
