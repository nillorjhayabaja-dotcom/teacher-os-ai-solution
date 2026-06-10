"""Security Metrics Service — Prometheus metrics for security observability.

Tracks and exposes security-related metrics:
- Authentication success/failure rates
- Token operations (issue, refresh, revoke)
- Rate limit hits and violations
- MFA usage and failures
- Session statistics
- Permission denied events
- Brute force detection events
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram

from backend.src.core.settings import settings


# ---------------------------------------------------------------------------
# Prometheus metric definitions
# ---------------------------------------------------------------------------

AUTH_ATTEMPTS = Counter(
    "teacheros_security_auth_attempts_total",
    "Total authentication attempts",
    ["status", "method"],  # status: success|failure, method: password|mfa|token
)

TOKEN_OPERATIONS = Counter(
    "teacheros_security_token_operations_total",
    "Token lifecycle operations",
    ["operation", "token_type"],  # operation: issue|refresh|revoke|blacklist
)

RATE_LIMIT_EVENTS = Counter(
    "teacheros_security_rate_limit_events_total",
    "Rate limit events",
    ["scope", "action"],  # action: hit|exceeded
)

ACTIVE_SESSIONS = Gauge(
    "teacheros_security_active_sessions",
    "Number of active user sessions",
    ["tenant_id"],
)

SESSION_CREATED = Counter(
    "teacheros_security_sessions_created_total",
    "Total sessions created",
)

SESSION_REVOKED = Counter(
    "teacheros_security_sessions_revoked_total",
    "Total sessions revoked",
)

MFA_OPERATIONS = Counter(
    "teacheros_security_mfa_operations_total",
    "MFA operations",
    ["operation", "status"],  # operation: setup|verify|disable
)

PERMISSION_DENIED = Counter(
    "teacheros_security_permission_denied_total",
    "Authorization denied events",
    ["permission", "tenant_id"],
)

BRUTE_FORCE_EVENTS = Counter(
    "teacheros_security_brute_force_events_total",
    "Brute force detection events",
    ["tenant_id"],
)

FILE_VALIDATION = Counter(
    "teacheros_security_file_validation_total",
    "File validation results",
    ["result"],  # result: allowed|rejected
)

SECURITY_EVENT_LATENCY = Histogram(
    "teacheros_security_event_latency_seconds",
    "Security event processing latency",
    ["event_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)

ACTIVE_MFA_USERS = Gauge(
    "teacheros_security_active_mfa_users",
    "Users with MFA enabled",
)

BLACKLISTED_TOKENS = Gauge(
    "teacheros_security_blacklisted_tokens",
    "Number of blacklisted tokens",
    ["token_type"],
)


@dataclass
class SecurityMetricsSnapshot:
    """Point-in-time snapshot of security metrics for dashboards."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    auth_attempts: Dict[str, int] = field(default_factory=dict)
    active_sessions: int = 0
    mfa_enabled_users: int = 0
    blacklisted_tokens: int = 0
    rate_limit_exceeded: int = 0
    permission_denied_count: int = 0
    brute_force_events: int = 0
    file_rejections: int = 0


class SecurityMetricsService:
    """Exposes security metrics to Prometheus and provides dashboard snapshots.

    All metrics are recorded via Prometheus client for real-time scraping.
    The snapshot method provides point-in-time data for admin dashboards.
    """

    def __init__(self) -> None:
        self._tenant_sessions: Dict[str, int] = {}
        self._mfa_user_count: int = 0
        self._blacklist_count_by_type: Dict[str, int] = {}
        self._snapshot_history: List[SecurityMetricsSnapshot] = []

    # ------------------------------------------------------------------
    # Authentication Metrics
    # ------------------------------------------------------------------
    def record_auth_attempt(
        self,
        status: str = "success",
        method: str = "password",
    ) -> None:
        """Record an authentication attempt.

        Args:
            status: 'success' or 'failure'
            method: 'password', 'mfa', or 'token'
        """
        AUTH_ATTEMPTS.labels(status=status, method=method).inc()

    def record_auth_success(self, method: str = "password") -> None:
        """Convenience: record a successful auth attempt."""
        self.record_auth_attempt(status="success", method=method)

    def record_auth_failure(self, method: str = "password") -> None:
        """Convenience: record a failed auth attempt."""
        self.record_auth_attempt(status="failure", method=method)

    # ------------------------------------------------------------------
    # Token Metrics
    # ------------------------------------------------------------------
    def record_token_operation(
        self,
        operation: str = "issue",
        token_type: str = "access",
    ) -> None:
        """Record a token lifecycle operation.

        Args:
            operation: 'issue', 'refresh', 'revoke', or 'blacklist'
            token_type: 'access' or 'refresh'
        """
        TOKEN_OPERATIONS.labels(operation=operation, token_type=token_type).inc()

    def set_blacklisted_token_count(self, count: int, token_type: str = "refresh") -> None:
        """Set the gauge for blacklisted tokens."""
        BLACKLISTED_TOKENS.labels(token_type=token_type).set(count)
        self._blacklist_count_by_type[token_type] = count

    # ------------------------------------------------------------------
    # Rate Limit Metrics
    # ------------------------------------------------------------------
    def record_rate_limit_hit(self, scope: str = "public") -> None:
        """Record a rate limit being reached."""
        RATE_LIMIT_EVENTS.labels(scope=scope, action="hit").inc()

    def record_rate_limit_exceeded(self, scope: str = "public") -> None:
        """Record a rate limit being exceeded."""
        RATE_LIMIT_EVENTS.labels(scope=scope, action="exceeded").inc()

    # ------------------------------------------------------------------
    # Session Metrics
    # ------------------------------------------------------------------
    def record_session_created(self, tenant_id: Optional[str] = None) -> None:
        """Record a new session creation."""
        SESSION_CREATED.inc()
        if tenant_id:
            self._tenant_sessions[tenant_id] = self._tenant_sessions.get(tenant_id, 0) + 1
            ACTIVE_SESSIONS.labels(tenant_id=tenant_id).set(
                self._tenant_sessions[tenant_id]
            )

    def record_session_revoked(self, tenant_id: Optional[str] = None) -> None:
        """Record a session revocation."""
        SESSION_REVOKED.inc()
        if tenant_id:
            current = self._tenant_sessions.get(tenant_id, 0)
            self._tenant_sessions[tenant_id] = max(0, current - 1)
            ACTIVE_SESSIONS.labels(tenant_id=tenant_id).set(
                self._tenant_sessions[tenant_id]
            )

    def set_active_session_count(self, count: int, tenant_id: str = "global") -> None:
        """Manually set the active session count for a tenant."""
        self._tenant_sessions[tenant_id] = count
        ACTIVE_SESSIONS.labels(tenant_id=tenant_id).set(count)

    # ------------------------------------------------------------------
    # MFA Metrics
    # ------------------------------------------------------------------
    def record_mfa_operation(
        self,
        operation: str = "setup",
        status: str = "success",
    ) -> None:
        """Record an MFA operation.

        Args:
            operation: 'setup', 'verify', or 'disable'
            status: 'success' or 'failure'
        """
        MFA_OPERATIONS.labels(operation=operation, status=status).inc()

    def set_mfa_enabled_user_count(self, count: int) -> None:
        """Set the gauge for users with MFA enabled."""
        ACTIVE_MFA_USERS.set(count)
        self._mfa_user_count = count

    # ------------------------------------------------------------------
    # Authorization Metrics
    # ------------------------------------------------------------------
    def record_permission_denied(
        self,
        permission: str = "unknown",
        tenant_id: Optional[str] = None,
    ) -> None:
        """Record an authorization denied event."""
        PERMISSION_DENIED.labels(
            permission=permission,
            tenant_id=tenant_id or "unknown",
        ).inc()

    # ------------------------------------------------------------------
    # Brute Force Metrics
    # ------------------------------------------------------------------
    def record_brute_force_event(self, tenant_id: Optional[str] = None) -> None:
        """Record a brute force detection event."""
        BRUTE_FORCE_EVENTS.labels(tenant_id=tenant_id or "unknown").inc()

    # ------------------------------------------------------------------
    # File Validation Metrics
    # ------------------------------------------------------------------
    def record_file_validation(self, allowed: bool = True) -> None:
        """Record a file validation result."""
        FILE_VALIDATION.labels(result="allowed" if allowed else "rejected").inc()

    # ------------------------------------------------------------------
    # Latency Tracking
    # ------------------------------------------------------------------
    def observe_security_event_latency(
        self,
        event_type: str,
        duration_seconds: float,
    ) -> None:
        """Observe the latency of a security event processing."""
        SECURITY_EVENT_LATENCY.labels(event_type=event_type).observe(duration_seconds)

    # ------------------------------------------------------------------
    # Dashboard Snapshot
    # ------------------------------------------------------------------
    def take_snapshot(self) -> SecurityMetricsSnapshot:
        """Take a point-in-time snapshot of all security metrics.

        Returns a SecurityMetricsSnapshot with current values for
        admin dashboard display.
        """
        snapshot = SecurityMetricsSnapshot(
            auth_attempts={
                "total": sum(
                    AUTH_ATTEMPTS.labels(status=s, method=m)._value.get()
                    for s in ("success", "failure")
                    for m in ("password", "mfa", "token")
                ),
                "success": sum(
                    AUTH_ATTEMPTS.labels(status="success", method=m)._value.get()
                    for m in ("password", "mfa", "token")
                ),
                "failure": sum(
                    AUTH_ATTEMPTS.labels(status="failure", method=m)._value.get()
                    for m in ("password", "mfa", "token")
                ),
            },
            active_sessions=sum(self._tenant_sessions.values()),
            mfa_enabled_users=self._mfa_user_count,
            blacklisted_tokens=sum(self._blacklist_count_by_type.values()),
            rate_limit_exceeded=sum(
                RATE_LIMIT_EVENTS.labels(scope=s, action="exceeded")._value.get()
                for s in ("public", "authenticated", "ai", "login")
            ),
            permission_denied_count=sum(
                PERMISSION_DENIED.labels(permission=p, tenant_id=t)._value.get()
                for p in ("unknown",)
                for t in ("unknown",)
            ),
            brute_force_events=sum(
                BRUTE_FORCE_EVENTS.labels(tenant_id=t)._value.get()
                for t in ("unknown",)
            ),
            file_rejections=sum(
                FILE_VALIDATION.labels(result="rejected")._value.get()
            ),
        )

        # Store for historical trending (keep last 100 snapshots)
        self._snapshot_history.append(snapshot)
        if len(self._snapshot_history) > 100:
            self._snapshot_history.pop(0)

        return snapshot

    def get_snapshot_history(
        self,
        limit: int = 20,
    ) -> List[SecurityMetricsSnapshot]:
        """Get recent metric snapshots for trend analysis."""
        return list(self._snapshot_history[-limit:])

    # ------------------------------------------------------------------
    # Bulk / Convenience Recording
    # ------------------------------------------------------------------
    def record_from_security_event(
        self,
        event_type: str,
        tenant_id: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> None:
        """Record metrics inferred from a security event type string.

        Maps common security event types to metric recording calls.
        """
        if duration_seconds is not None:
            self.observe_security_event_latency(event_type, duration_seconds)

        if event_type == "login.success":
            self.record_auth_success(method="password")
        elif event_type == "login.failed":
            self.record_auth_failure(method="password")
        elif event_type == "mfa.verified":
            self.record_mfa_operation(operation="verify", status="success")
        elif event_type == "mfa.failed":
            self.record_mfa_operation(operation="verify", status="failure")
        elif event_type == "token.revoke":
            self.record_token_operation(operation="revoke", token_type="access")
        elif event_type == "rate.limit.exceeded":
            self.record_rate_limit_exceeded()
        elif event_type == "session.created":
            self.record_session_created(tenant_id=tenant_id)
        elif event_type == "session.revoked":
            self.record_session_revoked(tenant_id=tenant_id)
        elif event_type == "brute_force.detected":
            self.record_brute_force_event(tenant_id=tenant_id)
        elif event_type == "file.validation.failed":
            self.record_file_validation(allowed=False)