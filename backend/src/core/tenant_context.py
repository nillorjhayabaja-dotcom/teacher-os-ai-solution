"""Thread‑local tenant context utilities.

Provides ``get_current_tenant`` and ``set_current_tenant`` functions that store
the tenant identifier in a ``contextvars.ContextVar``. This works for both sync
and async code.
"""

import contextvars
from typing import Optional

_current_tenant: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_tenant", default=None
)


def get_current_tenant() -> Optional[str]:
    """Return the tenant identifier for the current execution context."""
    return _current_tenant.get()


def set_current_tenant(tenant_id: Optional[str]) -> contextvars.Token[Optional[str]]:
    """Set (or clear) the tenant identifier for the current execution context."""
    return _current_tenant.set(tenant_id)


def reset_current_tenant(token: contextvars.Token[Optional[str]]) -> None:
    """Restore the tenant identifier to a previously captured context token."""
    _current_tenant.reset(token)


__all__ = ["get_current_tenant", "set_current_tenant", "reset_current_tenant"]