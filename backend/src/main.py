"""TeacherOS main application entry point.

Configures the FastAPI application with comprehensive security middleware:
- Request ID / Correlation ID tracking
- Rate limiting (SlowAPI)
- CSRF protection
- CORS security
- Multi-tenant isolation
- JWT authentication with blacklist/revocation
- RBAC authorization
"""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from backend.src.api import router as api_router
from backend.src.core.settings import settings
from backend.src.core.tenant_context import set_current_tenant, reset_current_tenant
from backend.src.security.jwt_service import JWTService
from backend.src.security.token_service import TokenService
from backend.src.security.rbac import RoleEngine, PermissionEngine, PolicyEngine, RBACService
from backend.src.security.request_id_middleware import RequestIDMiddleware
from backend.src.security.rate_limit_middleware import RateLimitMiddleware
from backend.src.security.csrf_middleware import CSRFMiddleware
from backend.src.multi_tenancy.tenant_middleware import TenantMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # ----------------------------------------------------------------------
    # Security Middleware Stack (order matters - first registered = outermost)
    # ----------------------------------------------------------------------

    # 1. Request ID / Correlation ID (outermost - runs first)
    app.add_middleware(RequestIDMiddleware)

    # 2. Rate Limiting (before authentication to protect auth endpoints)
    app.add_middleware(RateLimitMiddleware)

    # 3. CSRF Protection (for browser-based clients)
    if settings.ENVIRONMENT != "development":
        app.add_middleware(CSRFMiddleware)

    # 4. CORS (allowlisted origins only)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        expose_headers=settings.CORS_EXPOSE_HEADERS,
    )

    # 5. Multi-tenancy (extracts tenant context from headers)
    app.add_middleware(TenantMiddleware)

    # 6. Authentication & Authorization
    jwt_service = JWTService()
    token_service = TokenService(jwt_service=jwt_service)
    role_engine = RoleEngine()
    permission_engine = PermissionEngine()
    policy_engine = PolicyEngine(role_engine=role_engine, permission_engine=permission_engine)
    rbac_service = RBACService(
        role_engine=role_engine,
        permission_engine=permission_engine,
        policy_engine=policy_engine,
    )

    from backend.src.security.auth_middleware import AuthMiddleware

    app.add_middleware(
        AuthMiddleware,
        jwt_service=jwt_service,
        token_service=token_service,
        rbac_service=rbac_service,
    )

    # ----------------------------------------------------------------------
    # Store services on app state for route handlers
    # ----------------------------------------------------------------------
    app.state.jwt_service = jwt_service
    app.state.token_service = token_service
    app.state.rbac_service = rbac_service
    app.state.role_engine = role_engine
    app.state.permission_engine = permission_engine
    app.state.policy_engine = policy_engine

    # ----------------------------------------------------------------------
    # Routes
    # ----------------------------------------------------------------------
    app.include_router(api_router)

    # ----------------------------------------------------------------------
    # Startup / Shutdown events
    # ----------------------------------------------------------------------
    @app.on_event("startup")
    async def startup() -> None:
        """Initialize services on application startup."""
        # In production, initialize database connections, Redis, etc.
        pass

    @app.on_event("shutdown")
    async def shutdown() -> None:
        """Clean up resources on application shutdown."""
        pass

    return app


app = create_app()