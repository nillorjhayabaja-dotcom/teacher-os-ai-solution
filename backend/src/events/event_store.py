"""In‑memory event store used by the replay utility."""

from typing import List
from .base_domain_event import BaseDomainEvent


class EventStore:
    """Simple list‑based store for domain events."""

    def __init__(self) -> None:
        self._events: List[BaseDomainEvent] = []

    def append(self, event: BaseDomainEvent) -> None:
        """Add an event to the store."""
        self._events.append(event)

    def all(self) -> List[BaseDomainEvent]:
        """Return a copy of all stored events."""
        return list(self._events)


__all__ = ["EventStore"]