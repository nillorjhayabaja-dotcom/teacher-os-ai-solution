"""Settings and configuration API endpoints.

Provides read/write access to tenant and system settings.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.src.core.constants import PERM_SETTINGS_READ, PERM_SETTINGS_WRITE
from backend.src.core.settings import settings as app_settings
from backend.src.core.exceptions import InsufficientPermissionsError

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SystemSettings(BaseModel):
    app_name: str
    version: str
    environment: str
    debug: bool


class TenantSettings(BaseModel):
    tenant_id: str
    organization_name: Optional[str] = None
    school_name: Optional[str] = None
    school_year: Optional[str] = None
    grading_periods: int = 4
    passing_grade: float = 75.0
    attendance_required: bool = True
    features: Dict[str, bool] = {}


class TenantSettingsUpdate(BaseModel):
    organization_name: Optional[str] = None
    school_name: Optional[str] = None
    school_year: Optional[str] = None
    grading_periods: Optional[int] = None
    passing_grade: Optional[float] = None
    attendance_required: Optional[bool] = None
    features: Optional[Dict[str, bool]] = None


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_tenant_settings_db: Dict[str, Dict[str, Any]] = {}


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


@router.get("/system", response_model=SystemSettings)
def get_system_settings(request: Request):
    """Get system-wide settings."""
    _require_permission(request, PERM_SETTINGS_READ)

    return SystemSettings(
        app_name=app_settings.APP_NAME,
        version=app_settings.VERSION,
        environment=app_settings.ENVIRONMENT,
        debug=app_settings.DEBUG,
    )


@router.get("/tenant", response_model=TenantSettings)
def get_tenant_settings(request: Request):
    """Get settings for the current tenant."""
    _require_permission(request, PERM_SETTINGS_READ)

    tenant_id = getattr(request.state, "user_tenant_id", None) or "default"

    if tenant_id not in _tenant_settings_db:
        # Return defaults
        return TenantSettings(tenant_id=tenant_id)

    settings = _tenant_settings_db[tenant_id]
    return TenantSettings(
        tenant_id=tenant_id,
        organization_name=settings.get("organization_name"),
        school_name=settings.get("school_name"),
        school_year=settings.get("school_year"),
        grading_periods=settings.get("grading_periods", 4),
        passing_grade=settings.get("passing_grade", 75.0),
        attendance_required=settings.get("attendance_required", True),
        features=settings.get("features", {}),
    )


@router.put("/tenant", response_model=TenantSettings)
def update_tenant_settings(req: TenantSettingsUpdate, request: Request):
    """Update settings for the current tenant."""
    _require_permission(request, PERM_SETTINGS_WRITE)

    tenant_id = getattr(request.state, "user_tenant_id", None) or "default"

    if tenant_id not in _tenant_settings_db:
        _tenant_settings_db[tenant_id] = {}

    settings = _tenant_settings_db[tenant_id]

    if req.organization_name is not None:
        settings["organization_name"] = req.organization_name
    if req.school_name is not None:
        settings["school_name"] = req.school_name
    if req.school_year is not None:
        settings["school_year"] = req.school_year
    if req.grading_periods is not None:
        settings["grading_periods"] = req.grading_periods
    if req.passing_grade is not None:
        settings["passing_grade"] = req.passing_grade
    if req.attendance_required is not None:
        settings["attendance_required"] = req.attendance_required
    if req.features is not None:
        settings["features"] = req.features

    return get_tenant_settings(request)