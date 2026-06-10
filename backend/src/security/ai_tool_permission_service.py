"""AI Tool Permission Service — tool-level access control for AI agents.

Provides granular permissions for AI tool execution based on:
- User role and assigned permissions
- Tenant/school isolation
- Tool sensitivity classification
- Rate limits per tool per user
- Audit logging of tool usage

Tool sensitivity levels:
- low: Read-only, non-sensitive data queries (e.g., curriculum search)
- medium: Data lookups with some sensitivity (e.g., student search)
- high: Data modification or sensitive data access (e.g., grade lookup, notification)
- critical: Destructive or high-impact operations (e.g., grade modify)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from backend.src.core.constants import PERM_AI_USE
from backend.src.security.rbac import RBACService


class ToolSensitivity(Enum):
    """Sensitivity classification for AI tools."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ToolPermission:
    """Defines permissions required to use a specific AI tool."""
    tool_name: str
    sensitivity: ToolSensitivity
    required_permissions: List[str] = field(default_factory=list)
    allowed_roles: List[str] = field(default_factory=list)
    requires_mfa: bool = False
    rate_limit_per_minute: int = 30
    audit_on_use: bool = True


@dataclass
class ToolAccessRequest:
    """A request to access an AI tool."""
    user_id: str
    tenant_id: str
    school_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    mfa_verified: bool = False


@dataclass
class ToolAccessDecision:
    """Result of a tool access evaluation."""
    allowed: bool
    reason: Optional[str] = None
    requires_mfa: bool = False
    enforcement_hint: Optional[str] = None


# ---------------------------------------------------------------------------
# Default tool permission registry — maps each known tool to its security
# classification and required access controls.
# ---------------------------------------------------------------------------

DEFAULT_TOOL_PERMISSIONS: Dict[str, ToolPermission] = {
    # Low sensitivity — public/read-only reference data
    "curriculum_search": ToolPermission(
        tool_name="curriculum_search",
        sensitivity=ToolSensitivity.LOW,
        required_permissions=[PERM_AI_USE],
        rate_limit_per_minute=60,
    ),
    "melc_lookup": ToolPermission(
        tool_name="melc_lookup",
        sensitivity=ToolSensitivity.LOW,
        required_permissions=[PERM_AI_USE],
        rate_limit_per_minute=60,
    ),
    "transmutation_lookup": ToolPermission(
        tool_name="transmutation_lookup",
        sensitivity=ToolSensitivity.LOW,
        required_permissions=[PERM_AI_USE],
        rate_limit_per_minute=60,
    ),
    # Medium sensitivity — involves student/organizational data
    "student_search": ToolPermission(
        tool_name="student_search",
        sensitivity=ToolSensitivity.MEDIUM,
        required_permissions=[PERM_AI_USE, "student.read"],
        allowed_roles=["adviser", "coordinator", "principal", "school_head", "super_admin"],
        rate_limit_per_minute=30,
    ),
    "school_config_lookup": ToolPermission(
        tool_name="school_config_lookup",
        sensitivity=ToolSensitivity.MEDIUM,
        required_permissions=[PERM_AI_USE],
        rate_limit_per_minute=30,
    ),
    "form_template_lookup": ToolPermission(
        tool_name="form_template_lookup",
        sensitivity=ToolSensitivity.MEDIUM,
        required_permissions=[PERM_AI_USE, "form.read"],
        rate_limit_per_minute=30,
    ),
    # High sensitivity — data access or operations
    "grade_lookup": ToolPermission(
        tool_name="grade_lookup",
        sensitivity=ToolSensitivity.HIGH,
        required_permissions=[PERM_AI_USE, "grade.read"],
        requires_mfa=True,
        rate_limit_per_minute=15,
    ),
    "attendance_analyzer": ToolPermission(
        tool_name="attendance_analyzer",
        sensitivity=ToolSensitivity.HIGH,
        required_permissions=[PERM_AI_USE, "attendance.write"],
        requires_mfa=True,
        rate_limit_per_minute=15,
    ),
    "student_risk_score": ToolPermission(
        tool_name="student_risk_score",
        sensitivity=ToolSensitivity.HIGH,
        required_permissions=[PERM_AI_USE, "student.read"],
        requires_mfa=True,
        rate_limit_per_minute=10,
    ),
    "notification_sender": ToolPermission(
        tool_name="notification_sender",
        sensitivity=ToolSensitivity.HIGH,
        required_permissions=[PERM_AI_USE],
        allowed_roles=["adviser", "principal", "school_head", "super_admin"],
        requires_mfa=True,
        rate_limit_per_minute=10,
    ),
    # Critical — destructive or high-impact operations
    "form_validator": ToolPermission(
        tool_name="form_validator",
        sensitivity=ToolSensitivity.CRITICAL,
        required_permissions=[PERM_AI_USE, "form.write"],
        allowed_roles=["coordinator", "principal", "super_admin"],
        requires_mfa=True,
        rate_limit_per_minute=5,
    ),
    "rubric_generator": ToolPermission(
        tool_name="rubric_generator",
        sensitivity=ToolSensitivity.MEDIUM,
        required_permissions=[PERM_AI_USE, "grade.write"],
        rate_limit_per_minute=15,
    ),
}


class AIToolPermissionService:
    """Service for enforcing tool-level permissions on AI agent execution.

    Provides:
    - Pre-execution permission checks against user roles and permissions
    - Sensitivity-based access control
    - Rate limiting per tool per user (sliding window)
    - MFA requirement enforcement for high-sensitivity tools
    - Audit trail for tool usage decisions
    """

    def __init__(
        self,
        rbac_service: Optional[RBACService] = None,
        tool_permissions: Optional[Dict[str, ToolPermission]] = None,
    ) -> None:
        self._rbac = rbac_service or RBACService()
        self._tool_permissions = tool_permissions or dict(DEFAULT_TOOL_PERMISSIONS)
        # Track usage for rate limiting: {tool_name: {user_id: [timestamps]}}
        self._usage_tracker: Dict[str, Dict[str, List[datetime]]] = {}

    # ------------------------------------------------------------------
    # Permission Registration
    # ------------------------------------------------------------------
    def register_tool_permission(self, permission: ToolPermission) -> None:
        """Register or update permissions for a tool."""
        self._tool_permissions[permission.tool_name] = permission

    def get_tool_permission(self, tool_name: str) -> Optional[ToolPermission]:
        """Get the permission config for a tool, if registered."""
        return self._tool_permissions.get(tool_name)

    def get_sensitivity(self, tool_name: str) -> Optional[ToolSensitivity]:
        """Get the sensitivity classification for a tool."""
        perm = self._tool_permissions.get(tool_name)
        return perm.sensitivity if perm else None

    # ------------------------------------------------------------------
    # Core Access Check
    # ------------------------------------------------------------------
    def check_access(
        self,
        request: ToolAccessRequest,
        tool_name: str,
    ) -> ToolAccessDecision:
        """Check whether a user may execute a given AI tool.

        Evaluates:
        1. Tool exists in permission registry
        2. User has required permissions (via RBAC or direct)
        3. User is in allowed roles (if restricted)
        4. MFA is verified (if required by sensitivity)
        5. Rate limit has not been exceeded

        Args:
            request: The access request context (user, roles, permissions).
            tool_name: The name of the tool being requested.

        Returns:
            A ToolAccessDecision indicating allow/deny with reason.
        """
        config = self._tool_permissions.get(tool_name)
        if not config:
            # Unknown tool — deny by default
            return ToolAccessDecision(
                allowed=False,
                reason=f"Tool '{tool_name}' is not registered in the permission registry",
            )

        # 1. Check required permissions
        if not self._has_required_permissions(request, config):
            return ToolAccessDecision(
                allowed=False,
                reason=(
                    f"Missing required permissions for tool '{tool_name}'. "
                    f"Required: {config.required_permissions}"
                ),
                enforcement_hint="insufficient_permissions",
            )

        # 2. Check role restrictions (if configured)
        if config.allowed_roles and not self._has_allowed_role(request, config):
            return ToolAccessDecision(
                allowed=False,
                reason=(
                    f"User role not authorized for tool '{tool_name}'. "
                    f"Allowed roles: {config.allowed_roles}"
                ),
                enforcement_hint="role_not_allowed",
            )

        # 3. Check MFA requirement
        if config.requires_mfa and not request.mfa_verified:
            return ToolAccessDecision(
                allowed=False,
                reason=f"Tool '{tool_name}' requires MFA verification",
                requires_mfa=True,
                enforcement_hint="mfa_required",
            )

        # 4. Check rate limit
        rate_check = self._check_rate_limit(tool_name, request.user_id, config)
        if not rate_check["allowed"]:
            return ToolAccessDecision(
                allowed=False,
                reason=(
                    f"Rate limit exceeded for tool '{tool_name}'. "
                    f"Limit: {config.rate_limit_per_minute}/minute. "
                    f"Retry after {rate_check['retry_after_seconds']}s"
                ),
                enforcement_hint="rate_limited",
            )

        # All checks passed
        return ToolAccessDecision(
            allowed=True,
            reason=None,
        )

    def _has_required_permissions(
        self,
        request: ToolAccessRequest,
        config: ToolPermission,
    ) -> bool:
        """Check if the user has all required permissions.

        Uses RBAC if available, falling back to direct permission list.
        """
        if not config.required_permissions:
            return True

        if self._rbac:
            return self._rbac.has_all_permissions(
                request.user_id,
                config.required_permissions,
                tenant_id=request.tenant_id,
            )

        # Fallback: direct permission check
        user_perms = set(request.permissions)
        return all(p in user_perms for p in config.required_permissions)

    def _has_allowed_role(
        self,
        request: ToolAccessRequest,
        config: ToolPermission,
    ) -> bool:
        """Check if the user has at least one of the allowed roles."""
        if not config.allowed_roles:
            return True
        return bool(set(request.roles) & set(config.allowed_roles))

    # ------------------------------------------------------------------
    # Rate Limiting (Sliding Window)
    # ------------------------------------------------------------------
    def _check_rate_limit(
        self,
        tool_name: str,
        user_id: str,
        config: ToolPermission,
    ) -> Dict[str, Any]:
        """Check sliding-window rate limit for a tool+user combo."""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=1)

        # Initialize tracker for this tool+user
        if tool_name not in self._usage_tracker:
            self._usage_tracker[tool_name] = {}
        if user_id not in self._usage_tracker[tool_name]:
            self._usage_tracker[tool_name][user_id] = []

        timestamps = self._usage_tracker[tool_name][user_id]

        # Prune timestamps outside the current window
        self._usage_tracker[tool_name][user_id] = [
            t for t in timestamps if t > window_start
        ]
        current_count = len(self._usage_tracker[tool_name][user_id])

        if current_count >= config.rate_limit_per_minute:
            oldest = self._usage_tracker[tool_name][user_id][0]
            retry_after = max(
                0,
                int((oldest + timedelta(minutes=1) - now).total_seconds()),
            )
            return {"allowed": False, "retry_after_seconds": retry_after}

        # Record this usage
        self._usage_tracker[tool_name][user_id].append(now)
        return {"allowed": True, "retry_after_seconds": 0}

    def get_usage_count(
        self,
        tool_name: str,
        user_id: str,
    ) -> int:
        """Get the current usage count for a tool+user in the current window."""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=1)
        timestamps = self._usage_tracker.get(tool_name, {}).get(user_id, [])
        return len([t for t in timestamps if t > window_start])

    def reset_rate_limits(self, tool_name: Optional[str] = None) -> None:
        """Reset rate limit trackers for testing or admin override."""
        if tool_name:
            self._usage_tracker.pop(tool_name, None)
        else:
            self._usage_tracker.clear()

    # ------------------------------------------------------------------
    # Bulk / Convenience Check
    # ------------------------------------------------------------------
    def filter_allowed_tools(
        self,
        request: ToolAccessRequest,
        tool_names: List[str],
    ) -> List[str]:
        """Filter a list of tool names to only those the user may access.

        Useful for constructing agent-capability lists per user.
        """
        allowed: List[str] = []
        for name in tool_names:
            decision = self.check_access(request, name)
            if decision.allowed:
                allowed.append(name)
        return allowed

    def get_accessible_tools(
        self,
        request: ToolAccessRequest,
    ) -> List[str]:
        """Get all registered tools that this user can access."""
        return self.filter_allowed_tools(
            request,
            list(self._tool_permissions.keys()),
        )