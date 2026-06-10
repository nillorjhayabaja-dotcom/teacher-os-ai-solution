"""FastAPI style middleware that sets the current tenant in the context."""

from starlette.middleware.base import BaseHTTPMiddleware
from .tenant_context import TenantContext


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        tenant_id = request.headers.get("X-Tenant-Id", "default")
        TenantContext.set_current_tenant(tenant_id)
        response = await call_next(request)
        return response


__all__ = ["TenantMiddleware"]