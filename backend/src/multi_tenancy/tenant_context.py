"""Thin wrapper exposing core tenant helpers for the multi‑tenancy package."""

# Import core tenant helpers from the sibling package `src.core`.
from ..core.tenant_context import get_current_tenant, set_current_tenant


class TenantContext:
    @staticmethod
    def get_current_tenant():
        return get_current_tenant()

    @staticmethod
    def set_current_tenant(tenant_id):
        set_current_tenant(tenant_id)


__all__ = ["TenantContext"]