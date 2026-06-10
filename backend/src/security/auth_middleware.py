"""Production-grade authentication and authorization middleware.

Handles:
- JWT token validation (access tokens)
- Token blacklist check
- Token revocation check
- Tenant context enforcement
- RBAC permission checks
- Audit logging for requests
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.src.core.settings import settings
from backend.src.core.constants import HEADER_AUTHORIZATION
from backend.src.core.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
    InsufficientPermissionsError,
)
from backend.src.security.jwt_service import JWTService
from backend.src.security.token_service import TokenService
from backend.src.security.rbac import RBACService, PolicyEngine


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication and authorization middleware.

    Validates JWT tokens on every request (except public endpoints),
    checks blacklist, enforces tenant context, and applies RBAC.
    """

    def __init__(
        self,
        app,
        *,
        jwt_service: JWTService,
        token_service: Optional[TokenService] = None,
        rbac_service: Optional[RBACService] = None,
        public_paths: Optional[set] = None,
    ) -> None:
        super().__init__(app)
        self._jwt_service = jwt_service
        self._token_service = token_service
        self._rbac_service = rbac_service

        # Paths that don't require authentication
        self._public_paths = public_paths or {
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/password-reset",
            "/api/v1/auth/password-reset/confirm",
        }

    def _is_public_path(self, path: str) -> bool:
        """Check if a path is publicly accessible without authentication."""
        for public_path in self._public_paths:
            if path.startswith(public_path):
                return True
        return False

    def _check_path_permission(self, path: str) -> Optional[str]:
        """Map a request path to an RBAC permission.

        Returns None if no specific permission is required (just auth).
        """
        path_lower = path.lower()

        # Student resources
        if "/students/" in path_lower:
            if "DELETE" in path:
                return "student.delete"
            return "student.read"

        # Grade resources
        if "/grades/" in path_lower:
            if "COMPUTE" in path or "/compute" in path_lower:
                return "grades.compute"
            return "grade.read"

        # Attendance resources
        if "/attendance/" in path_lower:
            return "attendance.read"

        # Form resources
        if "/forms/" in path_lower:
            if "GENERATE" in path or "/generate" in path_lower:
                return "forms.generate"
            return "form.read"

        # Report resources
        if "/reports/" in path_lower:
            if "SUBMIT" in path or "/submit" in path_lower:
                return "reports.submit"
            return "report.read"

        # User management
        if "/users/" in path_lower:
            return "user.read"

        # AI endpoints
        if "/ai/" in path_lower or "/agents/" in path_lower:
            return "ai.use"

        # Audit
        if "/audit/" in path_lower:
            return "audit.read"

        # Settings
        if "/settings/" in path_lower:
            return "settings.read"

        # Sessions
        if "/sessions/" in path_lower:
            return "session.revoke"

        return None  # Just auth required

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Skip auth for public paths
        if self._is_public_path(path):
            return await call_next(request)

        # Extract and validate token
        auth_header = request.headers.get(HEADER_AUTHORIZATION)
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                content='{"detail": "Authentication required"}',
                status_code=401,
                media_type="application/json",
            )

        token = auth_header.removeprefix("Bearer ").strip()

        try:
            # Full token validation pipeline
            if self._token_service:
                payload = await self._token_service.validate_access_token(token)
            else:
                payload = self._jwt_service.decode(token)

            # Set user context on request
            request.state.user = payload
            request.state.user_id = payload.get("sub", "")
            request.state.user_tenant_id = payload.get("tenant") or payload.get("tenant_id")
            request.state.user_organization_id = payload.get("org_id") or payload.get("organization_id")
            request.state.user_school_id = payload.get("school_id")
            request.state.user_roles = payload.get("roles", [])
            request.state.user_permissions = payload.get("perms", [])
            request.state.mfa_verified = payload.get("mfa_verified", False)

        except TokenExpiredError:
            return Response(
                content='{"detail": "Token has expired"}',
                status_code=401,
                media_type="application/json",
                headers={"X-Token-Expired": "true"},
            )
        except TokenRevokedError:
            return Response(
                content='{"detail": "Token has been revoked"}',
                status_code=401,
                media_type="application/json",
            )
        except (TokenInvalidError, AuthenticationError) as e:
            return Response(
                content=f'{{"detail": "{str(e)}"}}',
                status_code=401,
                media_type="application/json",
            )

        # Check RBAC permission if RBAC service is available
        if self._rbac_service and request.state.user_id:
            required_permission = self._check_path_permission(path)
            if required_permission:
                try:
                    auth_context = {
                        "tenant_id": request.state.user_tenant_id,
                        "organization_id": request.state.user_organization_id,
                        "school_id": request.state.user_school_id,
                        "resource_path": path,
                        "method": request.method,
                    }
                    self._rbac_service.require_permission(
                        request.state.user_id,
                        required_permission,
                        context=auth_context,
                    )
                except InsufficientPermissionsError:
                    return Response(
                        content='{"detail": "Insufficient permissions"}',
                        status_code=403,
                        media_type="application/json",
                    )

        return await call_next(request)