"""User management API endpoints.

Provides user profile management, user listing, role management,
and user administration features.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.src.core.constants import (
    ROLE_TEACHER,
    ROLE_ADVISER,
    ROLE_COORDINATOR,
    ROLE_PRINCIPAL,
    ROLE_SCHOOL_HEAD,
    ROLE_DIVISION_STAFF,
    ROLE_SUPER_ADMIN,
    PERM_USER_READ,
    PERM_USER_WRITE,
    PERM_USER_DELETE,
    PERM_ROLE_READ,
    PERM_ROLE_WRITE,
)
from backend.src.core.exceptions import InsufficientPermissionsError, NotFoundError

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class UserProfile(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool = True
    mfa_enabled: bool = False
    organization_id: Optional[str] = None
    school_id: Optional[str] = None


class UserCreateRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=12)
    first_name: str
    last_name: str
    role: str = ROLE_TEACHER
    organization_id: Optional[str] = None
    school_id: Optional[str] = None


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserListResponse(BaseModel):
    users: List[UserProfile]
    total: int
    page: int
    page_size: int


class RoleAssignmentRequest(BaseModel):
    user_id: str
    role: str


# ---------------------------------------------------------------------------
# In-memory store (shared with auth module)
# ---------------------------------------------------------------------------

# We import the in-memory user DB from the auth module to keep consistency
from backend.src.api.v1.auth import _users_db, _get_user_or_404  # noqa: F401


def _require_user_permission(request: Request, permission: str) -> str:
    """Check permission and return user_id or raise 403."""
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


@router.get("", response_model=UserListResponse)
def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None,
):
    """List all users (paginated, filterable)."""
    _require_user_permission(request, PERM_USER_READ)

    users_list = list(_users_db.values())

    # Filter by role
    if role:
        users_list = [u for u in users_list if u["role"] == role]

    # Search by name or email
    if search:
        search_lower = search.lower()
        users_list = [
            u for u in users_list
            if search_lower in u["first_name"].lower()
            or search_lower in u["last_name"].lower()
            or search_lower in u["email"].lower()
        ]

    total = len(users_list)
    start = (page - 1) * page_size
    end = start + page_size
    page_users = users_list[start:end]

    return UserListResponse(
        users=[
            UserProfile(
                id=u["id"],
                email=u["email"],
                first_name=u["first_name"],
                last_name=u["last_name"],
                role=u["role"],
                is_active=u.get("is_active", True),
                mfa_enabled=u.get("mfa_enabled", False),
                organization_id=u.get("organization_id"),
                school_id=u.get("school_id"),
            )
            for u in page_users
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=UserProfile)
def get_user(user_id: str, request: Request):
    """Get a specific user's profile."""
    _require_user_permission(request, PERM_USER_READ)

    try:
        user = _get_user_or_404(user_id)
    except HTTPException:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(
        id=user["id"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        role=user["role"],
        is_active=user.get("is_active", True),
        mfa_enabled=user.get("mfa_enabled", False),
        organization_id=user.get("organization_id"),
        school_id=user.get("school_id"),
    )


@router.put("/{user_id}", response_model=UserProfile)
def update_user(user_id: str, req: UserUpdateRequest, request: Request):
    """Update a user's profile."""
    _require_user_permission(request, PERM_USER_WRITE)

    user = _get_user_or_404(user_id)

    if req.first_name is not None:
        user["first_name"] = req.first_name
    if req.last_name is not None:
        user["last_name"] = req.last_name
    if req.email is not None:
        # Check for duplicate email
        for uid, u in _users_db.items():
            if uid != user_id and u["email"] == req.email:
                raise HTTPException(status_code=409, detail="Email already in use")
        user["email"] = req.email
    if req.is_active is not None:
        user["is_active"] = req.is_active
    if req.role is not None:
        # Update RBAC role
        request.app.state.rbac_service.role_engine.set_user_roles(user_id, [req.role])
        user["role"] = req.role

    return UserProfile(
        id=user["id"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        role=user["role"],
        is_active=user.get("is_active", True),
        mfa_enabled=user.get("mfa_enabled", False),
        organization_id=user.get("organization_id"),
        school_id=user.get("school_id"),
    )


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: str, request: Request):
    """Deactivate a user account."""
    _require_user_permission(request, PERM_USER_DELETE)

    user = _get_user_or_404(user_id)
    user["is_active"] = False


@router.get("/{user_id}/roles", response_model=List[str])
def get_user_roles(user_id: str, request: Request):
    """Get all roles assigned to a user."""
    _require_user_permission(request, PERM_ROLE_READ)

    roles = request.app.state.rbac_service.get_user_roles(user_id)
    return list(roles)


@router.put("/{user_id}/roles", response_model=List[str])
def set_user_roles(user_id: str, req: List[str], request: Request):
    """Set roles for a user (replaces all existing roles)."""
    _require_user_permission(request, PERM_ROLE_WRITE)

    request.app.state.rbac_service.role_engine.set_user_roles(user_id, req)
    roles = request.app.state.rbac_service.get_user_roles(user_id)
    return list(roles)


@router.get("/{user_id}/permissions", response_model=List[str])
def get_user_permissions(user_id: str, request: Request):
    """Get all effective permissions for a user."""
    _require_user_permission(request, PERM_USER_READ)

    perms = request.app.state.rbac_service.get_user_permissions(user_id)
    return list(perms)