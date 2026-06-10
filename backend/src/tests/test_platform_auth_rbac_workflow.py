from __future__ import annotations

import pytest

from backend.src.security.jwt_service import JWTService
from backend.src.security.refresh_token_service import RefreshTokenService
from backend.src.security.rbac import PermissionEngine, RBAC, RoleEngine


def test_refresh_token_service_roundtrip():
    svc = RefreshTokenService()
    refresh = svc.create_refresh_token(subject="user-1", tenant_id="tenant-1")
    fetched = svc.get_refresh_token(refresh.token)
    assert fetched is not None
    assert fetched.subject == "user-1"
    assert fetched.tenant_id == "tenant-1"

    svc.revoke(refresh.token)
    assert svc.get_refresh_token(refresh.token) is None


def test_rbac_has_permission():
    role_engine = RoleEngine()
    permission_engine = PermissionEngine()

    role_engine.set_user_roles("user-1", ["teacher"])
    permission_engine.set_role_permissions("teacher", ["lesson.create"])

    rbac = RBAC(role_engine=role_engine, permission_engine=permission_engine)
    assert rbac.has_permission("user-1", "lesson.create") is True
    assert rbac.has_permission("user-1", "grade.compute") is False

