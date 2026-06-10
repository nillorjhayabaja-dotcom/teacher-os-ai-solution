"""Security package for TeacherOS.

Provides authentication, authorization, encryption, and security middleware.
"""

from backend.src.security.jwt_service import JWTService
from backend.src.security.token_service import TokenService
from backend.src.security.refresh_token_service import RefreshTokenService
from backend.src.security.password_service import PasswordService
from backend.src.security.mfa_service import MFAService
from backend.src.security.encryption_service import EncryptionService
from backend.src.security.session_service import SessionService
from backend.src.security.rbac import RBACService, RoleEngine, PermissionEngine, PolicyEngine
from backend.src.security.audit_service import AuditService
from backend.src.security.security_event_service import SecurityEventService
from backend.src.security.rate_limit_middleware import RateLimitMiddleware
from backend.src.security.csrf_middleware import CSRFMiddleware
from backend.src.security.request_id_middleware import RequestIDMiddleware
from backend.src.security.file_validation_service import FileValidationService
from backend.src.security.security_metrics_service import SecurityMetricsService, SecurityMetricsSnapshot
from backend.src.security.ai_tool_permission_service import (
    AIToolPermissionService,
    ToolPermission,
    ToolAccessRequest,
    ToolAccessDecision,
    ToolSensitivity,
    DEFAULT_TOOL_PERMISSIONS,
)

__all__ = [
    "JWTService",
    "TokenService",
    "RefreshTokenService",
    "PasswordService",
    "MFAService",
    "EncryptionService",
    "SessionService",
    "RBACService",
    "RoleEngine",
    "PermissionEngine",
    "PolicyEngine",
    "AuditService",
    "SecurityEventService",
    "SecurityMetricsService",
    "SecurityMetricsSnapshot",
    "AIToolPermissionService",
    "ToolPermission",
    "ToolAccessRequest",
    "ToolAccessDecision",
    "ToolSensitivity",
    "DEFAULT_TOOL_PERMISSIONS",
    "RateLimitMiddleware",
    "CSRFMiddleware",
    "RequestIDMiddleware",
    "FileValidationService",
]
