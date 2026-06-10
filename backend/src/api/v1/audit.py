"""Audit log API endpoints.

Provides read-only access to audit logs with filtering and pagination.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.src.core.constants import PERM_AUDIT_READ
from backend.src.core.exceptions import InsufficientPermissionsError

router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class AuditLogEntry(BaseModel):
    id: str
    action: str
    resource: str
    resource_id: Optional[str] = None
    actor_id: Optional[str] = None
    tenant_id: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: str


class AuditLogResponse(BaseModel):
    logs: List[AuditLogEntry]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# In-memory store (populated by events)
# ---------------------------------------------------------------------------

_audit_logs: List[Dict[str, Any]] = []


def record_audit_log(entry: Dict[str, Any]) -> None:
    """Record an audit log entry (called from security services)."""
    _audit_logs.append(entry)


def _require_permission(request: Request, permission: str) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        request.app.state.rbac_service.require_permission(user_id, permission)
    except InsufficientPermissionsError:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user_id


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=AuditLogResponse)
def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    resource: Optional[str] = None,
    actor_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """List audit logs with pagination and filtering."""
    _require_permission(request, PERM_AUDIT_READ)

    logs = list(_audit_logs)

    if action:
        logs = [l for l in logs if l.get("action") == action]
    if resource:
        logs = [l for l in logs if l.get("resource") == resource]
    if actor_id:
        logs = [l for l in logs if l.get("actor_id") == actor_id]
    if date_from:
        logs = [l for l in logs if l.get("timestamp", "") >= date_from]
    if date_to:
        logs = [l for l in logs if l.get("timestamp", "") <= date_to]

    # Sort by timestamp descending
    logs.sort(key=lambda l: l.get("timestamp", ""), reverse=True)

    total = len(logs)
    start = (page - 1) * page_size
    end = start + page_size
    page_logs = logs[start:end]

    return AuditLogResponse(
        logs=[
            AuditLogEntry(
                id=l.get("id", str(uuid4())),
                action=l.get("action", ""),
                resource=l.get("resource", ""),
                resource_id=l.get("resource_id"),
                actor_id=l.get("actor_id"),
                tenant_id=l.get("tenant_id"),
                details=l.get("details", {}),
                ip_address=l.get("ip_address"),
                user_agent=l.get("user_agent"),
                timestamp=l.get("timestamp", ""),
            )
            for l in page_logs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/actions")
def list_audit_actions():
    """List all distinct audit actions available."""
    actions = sorted(set(l.get("action", "") for l in _audit_logs))
    return {"actions": actions}


@router.get("/summary")
def get_audit_summary(request: Request):
    """Get a summary of audit activity."""
    _require_permission(request, PERM_AUDIT_READ)

    total = len(_audit_logs)
    actions: Dict[str, int] = {}
    for l in _audit_logs:
        action = l.get("action", "unknown")
        actions[action] = actions.get(action, 0) + 1

    return {
        "total_events": total,
        "action_counts": actions,
        "unique_actors": len(set(l.get("actor_id") for l in _audit_logs if l.get("actor_id"))),
    }