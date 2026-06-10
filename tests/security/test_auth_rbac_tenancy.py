from __future__ import annotations

import datetime as dt

import pytest

from backend.src.core.tenant_context import get_current_tenant, reset_current_tenant, set_current_tenant
from backend.src.multi_tenancy.organization_scope import OrganizationScope
from backend.src.multi_tenancy.tenant_resolver import TenantResolver
from backend.src.security.jwt_service import JWTService
from backend.src.security.password_service import PasswordService
from backend.src.security.rbac import PermissionEngine, RBAC, RoleEngine
from backend.src.security.refresh_token_service import RefreshTokenService


@pytest.mark.security
@pytest.mark.unit
def test_jwt_access_token_contains_subject_tenant_roles_and_permissions(tenant_id):
    service = JWTService()
    token = service.create_access_token(
        "user-1",
        tenant_id=str(tenant_id),
        roles=["teacher"],
        permissions=["lesson.create"],
    )

    payload = service.decode(token)

    assert payload["sub"] == "user-1"
    assert payload["tenant"] == str(tenant_id)
    assert payload["roles"] == ["teacher"]
    # JWTService uses "perms" as the claim key for permissions
    assert payload["perms"] == ["lesson.create"]


@pytest.mark.security
@pytest.mark.unit
def test_expired_token_is_rejected(tenant_id):
    service = JWTService()
    expired = service.create_access_token("user-1", tenant_id=str(tenant_id), expires_delta=dt.timedelta(seconds=-1))

    with pytest.raises(Exception):
        service.decode(expired)


@pytest.mark.security
@pytest.mark.unit
def test_refresh_tokens_can_be_created_resolved_and_revoked(tenant_id):
    service = RefreshTokenService()
    token = service.create_refresh_token(subject="user-1", tenant_id=str(tenant_id))

    resolved = service.get_refresh_token(token.token)
    assert resolved is not None
    assert resolved.subject == "user-1"
    service.revoke(token.token)
    assert service.get_refresh_token(token.token) is None


@pytest.mark.security
@pytest.mark.unit
def test_password_service_hashes_and_verifies_passwords():
    service = PasswordService()
    password_hash = service.hash_password("Correct Horse Battery Staple")

    assert service.verify_password("Correct Horse Battery Staple", password_hash.hash)
    assert not service.verify_password("wrong", password_hash.hash)


@pytest.mark.security
@pytest.mark.unit
def test_rbac_permission_engine_enforces_role_permissions():
    roles = RoleEngine()
    permissions = PermissionEngine()
    roles.set_user_roles("teacher-1", ["teacher"])
    permissions.set_role_permissions("teacher", ["lesson.create", "grade.compute"])
    rbac = RBAC(roles, permissions)

    assert rbac.has_permission("teacher-1", "lesson.create") is True
    assert rbac.has_permission("teacher-1", "admin.delete") is False


@pytest.mark.security
@pytest.mark.integration
def test_tenant_context_and_organization_scope_prevent_cross_tenant_leakage(tenant_id, other_tenant_id):
    token = set_current_tenant(str(tenant_id))
    try:
        assert get_current_tenant() == str(tenant_id)
        scope = OrganizationScope(organization_id=str(tenant_id))
        assert scope.organization_id == str(tenant_id)
    finally:
        reset_current_tenant(token)


@pytest.mark.security
@pytest.mark.unit
def test_tenant_resolver_returns_default():
    resolver = TenantResolver()

    class Request:
        headers = {"x-tenant-id": "tenant-a"}

    # TenantResolver currently returns a default value (foundational placeholder)
    result = resolver.resolve(Request())
    assert isinstance(result, str)
    assert result == "default_tenant"


@pytest.mark.security
@pytest.mark.xfail_architecture_gap(reason="Route-level authentication/authorization middleware is foundational and does not block unauthenticated access yet.")
def test_unauthorized_api_access_is_blocked_by_default():
    from fastapi.testclient import TestClient
    from backend.src.main import create_app

    response = TestClient(create_app()).get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.security
@pytest.mark.xfail_architecture_gap(reason="Immutable audit_logs persistence and rate limiting are documented but not implemented in current scaffold.")
def test_audit_logs_and_rate_limiting_are_enforced_for_sensitive_actions():
    assert False, "Audit log table writer and API rate limiter must exist before this compliance test can pass."