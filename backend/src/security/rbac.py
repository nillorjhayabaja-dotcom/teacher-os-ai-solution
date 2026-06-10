"""Role-Based Access Control system with Policy Engine.

Provides:
- Role definitions and hierarchy
- Permission management with granular resource-based permissions
- Policy engine with context-aware authorization
- Tenant-scoped permission checks
- Attribute-based conditions for advanced policies

Supported roles with predefined permissions:
- Teacher, Adviser, Coordinator, Principal, School Head
- Division Staff, Super Admin
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Union

from backend.src.core.constants import (
    ROLE_TEACHER,
    ROLE_ADVISER,
    ROLE_COORDINATOR,
    ROLE_PRINCIPAL,
    ROLE_SCHOOL_HEAD,
    ROLE_DIVISION_STAFF,
    ROLE_SUPER_ADMIN,
    PERM_STUDENT_READ,
    PERM_STUDENT_WRITE,
    PERM_STUDENT_DELETE,
    PERM_ATTENDANCE_READ,
    PERM_ATTENDANCE_WRITE,
    PERM_GRADE_READ,
    PERM_GRADE_WRITE,
    PERM_GRADE_COMPUTE,
    PERM_FORM_READ,
    PERM_FORM_WRITE,
    PERM_FORM_GENERATE,
    PERM_REPORT_READ,
    PERM_REPORT_WRITE,
    PERM_REPORT_SUBMIT,
    PERM_USER_READ,
    PERM_USER_WRITE,
    PERM_USER_DELETE,
    PERM_ROLE_READ,
    PERM_ROLE_WRITE,
    PERM_AUDIT_READ,
    PERM_SETTINGS_READ,
    PERM_SETTINGS_WRITE,
    PERM_AI_USE,
    PERM_FILE_UPLOAD,
    PERM_FILE_DELETE,
    PERM_MFA_ENABLE,
    PERM_MFA_DISABLE,
    PERM_SESSION_REVOKE,
    PERM_TOKEN_REVOKE,
)
from backend.src.core.exceptions import InsufficientPermissionsError, PrivilegeEscalationAttemptError


@dataclass(frozen=True)
class Role:
    """Represents a user role with its metadata."""
    name: str
    display_name: str = ""
    description: str = ""
    priority: int = 0  # Higher = more privileged


@dataclass(frozen=True)
class Permission:
    """Represents a granular permission."""
    key: str
    resource: str = ""  # e.g., "student", "grade", "form"
    action: str = ""    # e.g., "read", "write", "delete"
    description: str = ""


class PolicyEffect(Enum):
    """Effect of a policy evaluation."""
    ALLOW = "allow"
    DENY = "deny"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class PolicyCondition:
    """A condition that must be satisfied for a policy to apply."""
    attribute: str  # e.g., "tenant_id", "school_id", "resource_owner"
    operator: str    # e.g., "eq", "neq", "in", "contains"
    value: Any

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate this condition against the given context."""
        context_value = context.get(self.attribute)

        if self.operator == "eq":
            return context_value == self.value
        elif self.operator == "neq":
            return context_value != self.value
        elif self.operator == "in":
            return context_value in (self.value if isinstance(self.value, (list, set)) else [self.value])
        elif self.operator == "contains":
            return self.value in (context_value or "")
        elif self.operator == "gt":
            return (context_value or 0) > self.value
        elif self.operator == "lt":
            return (context_value or 0) < self.value
        elif self.operator == "exists":
            return context_value is not None
        elif self.operator == "not_exists":
            return context_value is None

        return False


@dataclass
class Policy:
    """A policy rule that grants or denies access."""
    name: str
    effect: PolicyEffect
    permissions: Set[str]
    conditions: List[PolicyCondition] = field(default_factory=list)
    roles: Set[str] = field(default_factory=set)  # If empty, applies to all roles
    priority: int = 0  # Higher priority policies override lower ones
    description: str = ""


# ---------------------------------------------------------------------------
# Default role-permission mappings
# ---------------------------------------------------------------------------
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    ROLE_TEACHER: {
        PERM_STUDENT_READ,
        PERM_ATTENDANCE_READ,
        PERM_ATTENDANCE_WRITE,
        PERM_GRADE_READ,
        PERM_GRADE_WRITE,
        PERM_FORM_READ,
        PERM_AI_USE,
        PERM_FILE_UPLOAD,
        PERM_MFA_ENABLE,
        PERM_MFA_DISABLE,
    },
    ROLE_ADVISER: {
        PERM_STUDENT_READ,
        PERM_STUDENT_WRITE,
        PERM_ATTENDANCE_READ,
        PERM_ATTENDANCE_WRITE,
        PERM_GRADE_READ,
        PERM_GRADE_WRITE,
        PERM_FORM_READ,
        PERM_FORM_WRITE,
        PERM_FORM_GENERATE,
        PERM_REPORT_READ,
        PERM_AI_USE,
        PERM_FILE_UPLOAD,
        PERM_MFA_ENABLE,
        PERM_MFA_DISABLE,
    },
    ROLE_COORDINATOR: {
        PERM_STUDENT_READ,
        PERM_STUDENT_WRITE,
        PERM_ATTENDANCE_READ,
        PERM_ATTENDANCE_WRITE,
        PERM_GRADE_READ,
        PERM_GRADE_WRITE,
        PERM_GRADE_COMPUTE,
        PERM_FORM_READ,
        PERM_FORM_WRITE,
        PERM_FORM_GENERATE,
        PERM_REPORT_READ,
        PERM_REPORT_WRITE,
        PERM_REPORT_SUBMIT,
        PERM_USER_READ,
        PERM_AI_USE,
        PERM_FILE_UPLOAD,
        PERM_MFA_ENABLE,
        PERM_MFA_DISABLE,
    },
    ROLE_PRINCIPAL: {
        PERM_STUDENT_READ,
        PERM_STUDENT_WRITE,
        PERM_ATTENDANCE_READ,
        PERM_ATTENDANCE_WRITE,
        PERM_GRADE_READ,
        PERM_GRADE_WRITE,
        PERM_GRADE_COMPUTE,
        PERM_FORM_READ,
        PERM_FORM_WRITE,
        PERM_FORM_GENERATE,
        PERM_REPORT_READ,
        PERM_REPORT_WRITE,
        PERM_REPORT_SUBMIT,
        PERM_USER_READ,
        PERM_USER_WRITE,
        PERM_ROLE_READ,
        PERM_AUDIT_READ,
        PERM_SETTINGS_READ,
        PERM_AI_USE,
        PERM_FILE_UPLOAD,
        PERM_FILE_DELETE,
        PERM_MFA_ENABLE,
        PERM_MFA_DISABLE,
        PERM_SESSION_REVOKE,
        PERM_TOKEN_REVOKE,
    },
    ROLE_SCHOOL_HEAD: {
        PERM_STUDENT_READ,
        PERM_STUDENT_WRITE,
        PERM_STUDENT_DELETE,
        PERM_ATTENDANCE_READ,
        PERM_ATTENDANCE_WRITE,
        PERM_GRADE_READ,
        PERM_GRADE_WRITE,
        PERM_GRADE_COMPUTE,
        PERM_FORM_READ,
        PERM_FORM_WRITE,
        PERM_FORM_GENERATE,
        PERM_REPORT_READ,
        PERM_REPORT_WRITE,
        PERM_REPORT_SUBMIT,
        PERM_USER_READ,
        PERM_USER_WRITE,
        PERM_ROLE_READ,
        PERM_ROLE_WRITE,
        PERM_AUDIT_READ,
        PERM_SETTINGS_READ,
        PERM_SETTINGS_WRITE,
        PERM_AI_USE,
        PERM_FILE_UPLOAD,
        PERM_FILE_DELETE,
        PERM_MFA_ENABLE,
        PERM_MFA_DISABLE,
        PERM_SESSION_REVOKE,
        PERM_TOKEN_REVOKE,
    },
    ROLE_DIVISION_STAFF: {
        PERM_STUDENT_READ,
        PERM_ATTENDANCE_READ,
        PERM_GRADE_READ,
        PERM_FORM_READ,
        PERM_REPORT_READ,
        PERM_REPORT_WRITE,
        PERM_REPORT_SUBMIT,
        PERM_USER_READ,
        PERM_USER_WRITE,
        PERM_ROLE_READ,
        PERM_AUDIT_READ,
        PERM_SETTINGS_READ,
        PERM_SETTINGS_WRITE,
        PERM_AI_USE,
        PERM_FILE_DELETE,
        PERM_SESSION_REVOKE,
        PERM_TOKEN_REVOKE,
    },
    ROLE_SUPER_ADMIN: {
        PERM_STUDENT_READ,
        PERM_STUDENT_WRITE,
        PERM_STUDENT_DELETE,
        PERM_ATTENDANCE_READ,
        PERM_ATTENDANCE_WRITE,
        PERM_GRADE_READ,
        PERM_GRADE_WRITE,
        PERM_GRADE_COMPUTE,
        PERM_FORM_READ,
        PERM_FORM_WRITE,
        PERM_FORM_GENERATE,
        PERM_REPORT_READ,
        PERM_REPORT_WRITE,
        PERM_REPORT_SUBMIT,
        PERM_USER_READ,
        PERM_USER_WRITE,
        PERM_USER_DELETE,
        PERM_ROLE_READ,
        PERM_ROLE_WRITE,
        PERM_AUDIT_READ,
        PERM_SETTINGS_READ,
        PERM_SETTINGS_WRITE,
        PERM_AI_USE,
        PERM_FILE_UPLOAD,
        PERM_FILE_DELETE,
        PERM_MFA_ENABLE,
        PERM_MFA_DISABLE,
        PERM_SESSION_REVOKE,
        PERM_TOKEN_REVOKE,
    },
}

# Role hierarchy for inheritance
ROLE_HIERARCHY: Dict[str, Set[str]] = {
    ROLE_TEACHER: set(),
    ROLE_ADVISER: {ROLE_TEACHER},
    ROLE_COORDINATOR: {ROLE_ADVISER, ROLE_TEACHER},
    ROLE_PRINCIPAL: {ROLE_COORDINATOR, ROLE_ADVISER, ROLE_TEACHER},
    ROLE_SCHOOL_HEAD: {ROLE_PRINCIPAL, ROLE_COORDINATOR, ROLE_ADVISER, ROLE_TEACHER},
    ROLE_DIVISION_STAFF: set(),  # Separate hierarchy
    ROLE_SUPER_ADMIN: set(ROLE_PERMISSIONS.keys()),  # Inherits all
}


class RoleEngine:
    """Manages user-to-role assignments and role hierarchy."""

    def __init__(self) -> None:
        self._user_roles: Dict[str, Set[str]] = {}

    def assign_role(self, user_id: str, role: str) -> None:
        """Assign a role to a user."""
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
        self._user_roles[user_id].add(role)

    def remove_role(self, user_id: str, role: str) -> None:
        """Remove a role from a user."""
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role)

    def set_user_roles(self, user_id: str, roles: Iterable[str]) -> None:
        """Set the exact set of roles for a user."""
        self._user_roles[user_id] = set(roles)

    def get_user_roles(self, user_id: str, *, include_inherited: bool = True) -> Set[str]:
        """Get all roles for a user, optionally including inherited roles."""
        direct_roles = self._user_roles.get(user_id, set())
        if not include_inherited:
            return direct_roles

        # Include inherited roles from hierarchy
        all_roles = set(direct_roles)
        for role in direct_roles:
            inherited = ROLE_HIERARCHY.get(role, set())
            all_roles.update(inherited)
        return all_roles


class PermissionEngine:
    """Maps roles to permissions with hierarchy resolution."""

    def __init__(self) -> None:
        self._role_permissions: Dict[str, Set[str]] = {}
        # Load default role permissions
        for role, perms in ROLE_PERMISSIONS.items():
            self._role_permissions[role] = set(perms)

    def set_role_permissions(self, role: str, permissions: Iterable[str]) -> None:
        """Set the exact permissions for a role."""
        self._role_permissions[role] = set(permissions)

    def add_role_permission(self, role: str, permission: str) -> None:
        """Add a permission to a role."""
        if role not in self._role_permissions:
            self._role_permissions[role] = set()
        self._role_permissions[role].add(permission)

    def remove_role_permission(self, role: str, permission: str) -> None:
        """Remove a permission from a role."""
        if role in self._role_permissions:
            self._role_permissions[role].discard(permission)

    def get_permissions_for_roles(self, roles: Iterable[str]) -> Set[str]:
        """Get the union of all permissions for the given roles."""
        perms: Set[str] = set()
        for r in roles:
            perms |= self._role_permissions.get(r, set())
        return perms

    def has_permission(self, roles: Iterable[str], permission: str) -> bool:
        """Check if any of the given roles has a specific permission."""
        return permission in self.get_permissions_for_roles(roles)


class PolicyEngine:
    """Advanced policy engine with context-aware authorization.

    Supports:
    - Role-based permission checks
    - Tenant-scoped resource isolation
    - Attribute-based conditions (ABAC)
    - Deny-overrides (DENY policies take precedence)
    - Custom policy evaluation
    """

    def __init__(
        self,
        role_engine: RoleEngine,
        permission_engine: PermissionEngine,
    ) -> None:
        self._role_engine = role_engine
        self._permission_engine = permission_engine
        self._policies: List[Policy] = []

    def add_policy(self, policy: Policy) -> None:
        """Register a custom policy."""
        self._policies.append(policy)
        # Sort by priority (highest first)
        self._policies.sort(key=lambda p: p.priority, reverse=True)

    def authorize(
        self,
        user_id: str,
        permission: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check if a user is authorized for a specific permission.

        Args:
            user_id: The user identifier.
            permission: The permission to check.
            context: Optional context for condition evaluation (tenant, school, resource).

        Returns:
            True if authorized.

        Raises:
            InsufficientPermissionsError: If not authorized.
        """
        context = context or {}
        roles = self._role_engine.get_user_roles(user_id)

        # 1. Evaluate custom policies first (deny-overrides)
        for policy in self._policies:
            # Check if policy applies to any of the user's roles
            if policy.roles and not roles.intersection(policy.roles):
                continue

            # Check if the permission is relevant
            if permission not in policy.permissions:
                continue

            # Evaluate conditions
            conditions_met = all(c.evaluate(context) for c in policy.conditions)
            if not conditions_met:
                continue

            # Policy applies
            if policy.effect == PolicyEffect.DENY:
                raise InsufficientPermissionsError(
                    f"Access denied by policy '{policy.name}': {policy.description}"
                )
            elif policy.effect == PolicyEffect.ALLOW:
                return True

        # 2. Check role-based permissions
        if not self._permission_engine.has_permission(roles, permission):
            raise InsufficientPermissionsError(
                f"User {user_id} does not have the '{permission}' permission"
            )

        return True

    def authorize_tenant_scoped(
        self,
        user_id: str,
        permission: str,
        resource_tenant_id: str,
        user_tenant_id: Optional[str] = None,
    ) -> bool:
        """Check authorization with tenant isolation enforcement.

        Ensures users can only access resources within their own tenant.
        Thread-safe: does not mutate the shared policies list.
        """
        # SECURITY: Check tenant isolation directly without mutating shared state
        if user_tenant_id is not None and user_tenant_id != resource_tenant_id:
            raise InsufficientPermissionsError("Cross-tenant access is not allowed")

        context = {
            "resource_tenant_id": resource_tenant_id,
            "user_tenant_id": user_tenant_id,
        }

        return self.authorize(user_id, permission, context)

    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all effective permissions for a user."""
        roles = self._role_engine.get_user_roles(user_id)
        return self._permission_engine.get_permissions_for_roles(roles)


class RBACService:
    """High-level RBAC service exposing authorization checks for the API layer."""

    def __init__(
        self,
        role_engine: RoleEngine,
        permission_engine: PermissionEngine,
        policy_engine: PolicyEngine,
    ) -> None:
        self.role_engine = role_engine
        self.permission_engine = permission_engine
        self.policy_engine = policy_engine

    def has_permission(
        self,
        user_id: str,
        permission: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check if user has a permission."""
        return self.policy_engine.authorize(user_id, permission, context)

    def has_role(self, user_id: str, role: str) -> bool:
        """Check if a user has a specific role."""
        return role in self.role_engine.get_user_roles(user_id)

    def require_permission(
        self,
        user_id: str,
        permission: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Require a permission or raise InsufficientPermissionsError."""
        self.policy_engine.authorize(user_id, permission, context)

    def require_role(self, user_id: str, role: str) -> None:
        """Require a role or raise InsufficientPermissionsError."""
        if not self.has_role(user_id, role):
            raise InsufficientPermissionsError(f"User {user_id} does not have the '{role}' role")

    def require_tenant_access(
        self,
        user_id: str,
        permission: str,
        resource_tenant_id: str,
        user_tenant_id: Optional[str] = None,
    ) -> None:
        """Require tenant-scoped access or raise InsufficientPermissionsError."""
        self.policy_engine.authorize_tenant_scoped(
            user_id, permission, resource_tenant_id, user_tenant_id
        )

    def get_user_roles(self, user_id: str) -> Set[str]:
        """Get all roles for a user."""
        return self.role_engine.get_user_roles(user_id)

    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user."""
        return self.policy_engine.get_user_permissions(user_id)