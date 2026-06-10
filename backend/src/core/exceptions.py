"""Common application exceptions used throughout the platform."""


class ApplicationError(Exception):
    """Base class for all domain‑specific errors."""


class NotFoundError(ApplicationError):
    """Raised when a requested resource cannot be found."""


class ConflictError(ApplicationError):
    """Raised when an operation would cause a conflict (e.g., duplicate)."""


class UnauthorizedError(ApplicationError):
    """Raised when authentication succeeds but permission is insufficient."""


# ---------------------------------------------------------------------------
# Security-specific exceptions
# ---------------------------------------------------------------------------

class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""


class TokenExpiredError(AuthenticationError):
    """Raised when a JWT token has expired."""


class TokenInvalidError(AuthenticationError):
    """Raised when a JWT token is invalid or malformed."""


class TokenRevokedError(AuthenticationError):
    """Raised when a JWT token has been revoked."""


class TokenReuseDetectedError(AuthenticationError):
    """Raised when a refresh token has been reused (rotation)."""


class MFANotEnabledError(AuthenticationError):
    """Raised when MFA is required but not enabled."""


class MFAVerificationFailedError(AuthenticationError):
    """Raised when MFA verification fails."""


class AuthorizationError(ApplicationError):
    """Raised when a user lacks the required permissions."""


class InsufficientPermissionsError(AuthorizationError):
    """Raised when the user's role lacks the required permission."""


class PrivilegeEscalationAttemptError(AuthorizationError):
    """Raised when an attempt to escalate privileges is detected."""


class TenantMismatchError(AuthorizationError):
    """Raised when a cross-tenant access attempt is detected."""


class RateLimitExceededError(ApplicationError):
    """Raised when a rate limit is exceeded."""


class SessionExpiredError(ApplicationError):
    """Raised when a session has expired."""


class SessionRevokedError(ApplicationError):
    """Raised when a session has been revoked."""


class FileValidationError(ApplicationError):
    """Raised when file validation fails."""


class FileSizeExceededError(FileValidationError):
    """Raised when the file size exceeds the maximum allowed."""


class FileTypeNotAllowedError(FileValidationError):
    """Raised when the file type is not allowed."""


class MalwareDetectedError(FileValidationError):
    """Raised when malware is detected in a file."""


class PromptInjectionDetectedError(ApplicationError):
    """Raised when prompt injection is detected in AI input."""


class CrossTenantContextLeakError(ApplicationError):
    """Raised when AI context from one tenant leaks to another."""


class DataRetentionViolationError(ApplicationError):
    """Raised when data retention policies are violated."""


class EncryptionError(ApplicationError):
    """Raised when encryption or decryption fails."""


class AuditLogError(ApplicationError):
    """Raised when audit logging fails."""