"""Immutable audit logging service.

Provides append-only audit logging for tracking:
- Authentication events (login, logout, password changes)
- Data modifications (grade changes, attendance updates)
- Form operations (generation, submission)
- AI agent usage
- Security events

Uses an append-only pattern where existing log entries cannot be modified.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.src.core.settings import settings
from backend.src.core.constants import (
    AUDIT_ACTION_CREATE,
    AUDIT_ACTION_READ,
    AUDIT_ACTION_UPDATE,
    AUDIT_ACTION_DELETE,
    AUDIT_ACTION_LOGIN,
    AUDIT_ACTION_LOGOUT,
    AUDIT_ACTION_EXPORT,
)
from backend.src.core.exceptions import AuditLogError


@dataclass
class AuditEntry:
    """An immutable audit log entry."""
    id: str
    timestamp: datetime
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    tenant_id: Optional[str] = None
    organization_id: Optional[str] = None
    school_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    severity: str = "info"  # info, warning, error, critical
    outcome: str = "success"  # success, failure


class AuditService:
    """Append-only audit logging service.

    Logs are stored in PostgreSQL (production) with an in-memory fallback.
    Entries are immutable once created - no update or delete operations.
    """

    def __init__(self, db_session: Optional[Any] = None) -> None:
        self._db = db_session
        self._entries: List[AuditEntry] = []  # In-memory fallback
        self._entries_by_user: Dict[str, List[str]] = {}  # user_id -> [entry_ids]

    # ---------------------------------------------------------------------
    # Log Creation
    # ---------------------------------------------------------------------
    def log(
        self,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        *,
        tenant_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        school_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        severity: str = "info",
        outcome: str = "success",
    ) -> AuditEntry:
        """Create an immutable audit log entry.

        Args:
            actor_id: The user who performed the action.
            action: The action performed (e.g., LOGIN, UPDATE, DELETE).
            resource_type: The type of resource (e.g., "grade", "student", "form").
            resource_id: The identifier of the resource.
            tenant_id: Tenant context.
            organization_id: Organization context.
            school_id: School context.
            details: Additional contextual data.
            ip_address: Client IP address.
            user_agent: User-Agent header.
            request_id: Request identifier for correlation.
            correlation_id: Correlation identifier for tracing.
            severity: Log severity level.
            outcome: Whether the action succeeded or failed.

        Returns:
            The created AuditEntry.

        Raises:
            AuditLogError: If the log cannot be written.
        """
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
            organization_id=organization_id,
            school_id=school_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            correlation_id=correlation_id,
            severity=severity,
            outcome=outcome,
        )

        try:
            self._persist_entry(entry)
        except Exception as e:
            raise AuditLogError(f"Failed to write audit log: {str(e)}")

        # Track by user
        if actor_id not in self._entries_by_user:
            self._entries_by_user[actor_id] = []
        self._entries_by_user[actor_id].append(entry.id)

        return entry

    def _persist_entry(self, entry: AuditEntry) -> None:
        """Persist an audit entry to the database."""
        if self._db:
            # In production, write to the audit_logs table
            # This uses SQLAlchemy to insert into append-only log table
            self._db.execute(
                "INSERT INTO audit_logs (id, timestamp, actor_id, action, "
                "resource_type, resource_id, tenant_id, organization_id, "
                "school_id, details, ip_address, user_agent, request_id, "
                "correlation_id, severity, outcome) "
                "VALUES (:id, :timestamp, :actor_id, :action, :resource_type, "
                ":resource_id, :tenant_id, :organization_id, :school_id, "
                ":details, :ip_address, :user_agent, :request_id, "
                ":correlation_id, :severity, :outcome)",
                {
                    "id": entry.id,
                    "timestamp": entry.timestamp,
                    "actor_id": entry.actor_id,
                    "action": entry.action,
                    "resource_type": entry.resource_type,
                    "resource_id": entry.resource_id,
                    "tenant_id": entry.tenant_id,
                    "organization_id": entry.organization_id,
                    "school_id": entry.school_id,
                    "details": json.dumps(entry.details) if entry.details else None,
                    "ip_address": entry.ip_address,
                    "user_agent": entry.user_agent,
                    "request_id": entry.request_id,
                    "correlation_id": entry.correlation_id,
                    "severity": entry.severity,
                    "outcome": entry.outcome,
                },
            )
        else:
            self._entries.append(entry)

    # ---------------------------------------------------------------------
    # Query Methods
    # ---------------------------------------------------------------------
    def get_entries_for_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEntry]:
        """Get audit entries for a specific user."""
        if self._db:
            result = self._db.execute(
                "SELECT * FROM audit_logs WHERE actor_id = :user_id "
                "ORDER BY timestamp DESC LIMIT :limit OFFSET :offset",
                {"user_id": user_id, "limit": limit, "offset": offset},
            )
            return [self._row_to_entry(row) for row in result.fetchall()]

        entry_ids = self._entries_by_user.get(user_id, [])[offset:offset + limit]
        return [e for e in self._entries if e.id in entry_ids]

    def get_entries_for_resource(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Get audit entries for a specific resource."""
        if self._db:
            result = self._db.execute(
                "SELECT * FROM audit_logs WHERE resource_type = :resource_type "
                "AND resource_id = :resource_id ORDER BY timestamp DESC LIMIT :limit",
                {"resource_type": resource_type, "resource_id": resource_id, "limit": limit},
            )
            return [self._row_to_entry(row) for row in result.fetchall()]

        return [
            e for e in self._entries
            if e.resource_type == resource_type and e.resource_id == resource_id
        ][:limit]

    def get_entries_for_tenant(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEntry]:
        """Get audit entries for a tenant."""
        if self._db:
            result = self._db.execute(
                "SELECT * FROM audit_logs WHERE tenant_id = :tenant_id "
                "ORDER BY timestamp DESC LIMIT :limit OFFSET :offset",
                {"tenant_id": tenant_id, "limit": limit, "offset": offset},
            )
            return [self._row_to_entry(row) for row in result.fetchall()]

        return [
            e for e in self._entries
            if e.tenant_id == tenant_id
        ][offset:offset + limit]

    def get_entries_by_action(
        self,
        action: str,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Get audit entries by action type."""
        if self._db:
            result = self._db.execute(
                "SELECT * FROM audit_logs WHERE action = :action "
                "ORDER BY timestamp DESC LIMIT :limit",
                {"action": action, "limit": limit},
            )
            return [self._row_to_entry(row) for row in result.fetchall()]

        return [e for e in self._entries if e.action == action][:limit]

    def get_recent_entries(self, limit: int = 50) -> List[AuditEntry]:
        """Get the most recent audit entries."""
        if self._db:
            result = self._db.execute(
                "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT :limit",
                {"limit": limit},
            )
            return [self._row_to_entry(row) for row in result.fetchall()]

        return sorted(self._entries, key=lambda e: e.timestamp, reverse=True)[:limit]

    def count_entries(self, tenant_id: Optional[str] = None) -> int:
        """Count audit entries, optionally filtered by tenant."""
        if self._db:
            if tenant_id:
                result = self._db.execute(
                    "SELECT COUNT(*) FROM audit_logs WHERE tenant_id = :tenant_id",
                    {"tenant_id": tenant_id},
                )
            else:
                result = self._db.execute("SELECT COUNT(*) FROM audit_logs")
            return result.scalar()

        if tenant_id:
            return len([e for e in self._entries if e.tenant_id == tenant_id])
        return len(self._entries)

    def _row_to_entry(self, row: Any) -> AuditEntry:
        """Convert a database row to an AuditEntry."""
        return AuditEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            actor_id=row["actor_id"],
            action=row["action"],
            resource_type=row["resource_type"],
            resource_id=row["resource_id"],
            tenant_id=row.get("tenant_id"),
            organization_id=row.get("organization_id"),
            school_id=row.get("school_id"),
            details=json.loads(row["details"]) if row.get("details") else None,
            ip_address=row.get("ip_address"),
            user_agent=row.get("user_agent"),
            request_id=row.get("request_id"),
            correlation_id=row.get("correlation_id"),
            severity=row.get("severity", "info"),
            outcome=row.get("outcome", "success"),
        )

    # ---------------------------------------------------------------------
    # Convenience Methods
    # ---------------------------------------------------------------------
    def log_login(
        self,
        user_id: str,
        *,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
    ) -> AuditEntry:
        """Log a login attempt."""
        return self.log(
            actor_id=user_id,
            action=AUDIT_ACTION_LOGIN,
            resource_type="session",
            resource_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            outcome="success" if success else "failure",
        )

    def log_logout(
        self,
        user_id: str,
        *,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditEntry:
        """Log a logout."""
        return self.log(
            actor_id=user_id,
            action=AUDIT_ACTION_LOGOUT,
            resource_type="session",
            resource_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
        )

    def log_data_change(
        self,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        *,
        tenant_id: Optional[str] = None,
        school_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditEntry:
        """Log a data modification event (create, update, delete)."""
        return self.log(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
            school_id=school_id,
            details=details,
            ip_address=ip_address,
            request_id=request_id,
        )