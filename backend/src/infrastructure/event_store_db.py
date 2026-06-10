from __future__ import annotations

"""DB-backed event store scaffold.

This repository phase does not include real SQLAlchemy integration.
A production implementation should persist events in PostgreSQL with
append-only semantics and tenant-scoped queries.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from backend.src.events.base_domain_event import BaseDomainEvent


@dataclass(frozen=True)
class StoredEvent:
    id: str
    tenant_id: str
    event_type: str
    payload: Dict[str, Any]


class DBEventStore:
    def __init__(self) -> None:
        self._events: List[StoredEvent] = []

    def append(self, *, tenant_id: str, event: BaseDomainEvent) -> None:
        self._events.append(
            StoredEvent(
                id=getattr(event, "event_id", ""),
                tenant_id=tenant_id,
                event_type=type(event).__name__,
                payload=getattr(event, "payload", {}) or {},
            )
        )

    def all(self, *, tenant_id: str) -> List[StoredEvent]:
        return [e for e in self._events if e.tenant_id == tenant_id]

