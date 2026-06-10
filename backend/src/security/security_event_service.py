"""Security event detection and management service.

Tracks and analyzes security events for threat detection:
- Failed logins and brute force attempts
- Privilege escalation attempts
- Cross-tenant access attempts
- Token reuse (theft) detection
- Rate limit violations
- Suspicious activity patterns
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from backend.src.core.settings import settings
from backend.src.core.constants import (
    EVENT_LOGIN_FAILED,
    EVENT_LOGIN_SUCCESS,
    EVENT_PRIVILEGE_ESCALATION_ATTEMPT,
    EVENT_CROSS_TENANT_ACCESS_ATTEMPT,
    EVENT_TOKEN_REUSE_DETECTED,
    EVENT_RATE_LIMIT_EXCEEDED,
    EVENT_AI_PROMPT_INJECTION_DETECTED,
)


@dataclass
class SecurityEvent:
    """A detected security event."""
    id: str
    event_type: str
    severity: str  # low, medium, high, critical
    actor_id: Optional[str] = None
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None


class SecurityEventService:
    """Security event detection and management.

    Detects suspicious patterns and tracks security events for
    investigation and response.
    """

    def __init__(self, redis_client: Optional[Any] = None) -> None:
        self._redis = redis_client
        self._events: List[SecurityEvent] = []

    # ---------------------------------------------------------------------
    # Event Creation
    # ---------------------------------------------------------------------
    def record_event(
        self,
        event_type: str,
        severity: str,
        *,
        actor_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> SecurityEvent:
        """Record a security event."""
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            severity=severity,
            actor_id=actor_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
        self._events.append(event)

        # Trigger detection rules
        self._detect_pattern(event)

        return event

    # ---------------------------------------------------------------------
    # Pattern Detection
    # ---------------------------------------------------------------------
    def _detect_pattern(self, event: SecurityEvent) -> None:
        """Run detection rules on a new event."""
        if event.event_type == EVENT_LOGIN_FAILED:
            self._detect_brute_force(event)
        elif event.event_type == EVENT_PRIVILEGE_ESCALATION_ATTEMPT:
            self._escalate_severity(event, "high")
        elif event.event_type == EVENT_CROSS_TENANT_ACCESS_ATTEMPT:
            self._escalate_severity(event, "high")
        elif event.event_type == EVENT_TOKEN_REUSE_DETECTED:
            self._escalate_severity(event, "critical")
        elif event.event_type == EVENT_AI_PROMPT_INJECTION_DETECTED:
            self._escalate_severity(event, "high")

    def _detect_brute_force(self, event: SecurityEvent) -> None:
        """Detect brute force login attempts."""
        if not event.actor_id and not event.ip_address:
            return

        recent_failures = self._get_recent_failures(
            actor_id=event.actor_id,
            ip_address=event.ip_address,
            minutes=5,
        )

        # Alert if more than 5 failures in 5 minutes
        if len(recent_failures) >= 5:
            alert = SecurityEvent(
                id=str(uuid.uuid4()),
                event_type="brute_force.detected",
                severity="critical",
                actor_id=event.actor_id,
                tenant_id=event.tenant_id,
                ip_address=event.ip_address,
                details={
                    "failure_count": len(recent_failures),
                    "time_window_minutes": 5,
                    "triggering_event": event.id,
                    "recent_failures": [e.id for e in recent_failures],
                },
            )
            self._events.append(alert)

    def _get_recent_failures(
        self,
        actor_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        minutes: int = 5,
    ) -> List[SecurityEvent]:
        """Get recent failed login events."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [
            e for e in self._events
            if e.event_type == EVENT_LOGIN_FAILED
            and e.timestamp > cutoff
            and (
                (actor_id and e.actor_id == actor_id)
                or (ip_address and e.ip_address == ip_address)
            )
        ]

    def _escalate_severity(self, event: SecurityEvent, severity: str) -> None:
        """Escalate the severity of an event."""
        if severity == "critical":
            event.severity = "critical"
        elif severity == "high" and event.severity not in ("critical",):
            event.severity = "high"
        elif severity == "medium" and event.severity not in ("critical", "high"):
            event.severity = "medium"

    # ---------------------------------------------------------------------
    # Event Queries
    # ---------------------------------------------------------------------
    def get_events(
        self,
        *,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        actor_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        unresolved_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SecurityEvent]:
        """Query security events with filters."""
        filtered = self._events

        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        if severity:
            filtered = [e for e in filtered if e.severity == severity]
        if actor_id:
            filtered = [e for e in filtered if e.actor_id == actor_id]
        if tenant_id:
            filtered = [e for e in filtered if e.tenant_id == tenant_id]
        if unresolved_only:
            filtered = [e for e in filtered if not e.resolved]

        # Sort by timestamp descending
        filtered.sort(key=lambda e: e.timestamp, reverse=True)

        return filtered[offset:offset + limit]

    def get_event_by_id(self, event_id: str) -> Optional[SecurityEvent]:
        """Get a specific security event by ID."""
        for event in self._events:
            if event.id == event_id:
                return event
        return None

    def resolve_event(self, event_id: str, resolution: str) -> bool:
        """Mark a security event as resolved.

        Args:
            event_id: The event identifier.
            resolution: Description of how the event was resolved.

        Returns:
            True if the event was found and resolved.
        """
        event = self.get_event_by_id(event_id)
        if not event:
            return False

        event.resolved = True
        event.resolved_at = datetime.now(timezone.utc)
        event.resolution = resolution
        return True

    # ---------------------------------------------------------------------
    # Dashboard / Summary
    # ---------------------------------------------------------------------
    def get_event_summary(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of security events for dashboard display."""
        events = self._events
        if tenant_id:
            events = [e for e in events if e.tenant_id == tenant_id]

        return {
            "total_events": len(events),
            "unresolved_events": len([e for e in events if not e.resolved]),
            "by_severity": {
                "critical": len([e for e in events if e.severity == "critical"]),
                "high": len([e for e in events if e.severity == "high"]),
                "medium": len([e for e in events if e.severity == "medium"]),
                "low": len([e for e in events if e.severity == "low"]),
            },
            "by_type": self._count_by_type(events),
            "recent_critical": [
                e for e in events
                if e.severity in ("critical", "high")
                and not e.resolved
            ][:10],
        }

    def _count_by_type(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Count events by type."""
        counts: Dict[str, int] = {}
        for e in events:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1
        return counts