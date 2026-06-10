from __future__ import annotations

from typing import Any, Dict

from fastapi import Request

from backend.src.security.rbac import Permission


def get_request_user(request: Request) -> Dict[str, Any] | None:
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return dict(user)


def get_tenant_id(request: Request) -> str | None:
    return getattr(request.state, "tenant_id", None)

