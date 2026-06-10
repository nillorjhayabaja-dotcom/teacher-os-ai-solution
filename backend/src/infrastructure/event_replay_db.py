from __future__ import annotations

"""DB-backed event replay scaffold."""

from typing import Any

from backend.src.core.tenant_context import get_current_tenant
from backend.src.events.event_dispatcher import EventDispatcher

from .event_store_db import DBEventStore


class DBEventReplay:
    def __init__(self, store: DBEventStore, dispatcher: EventDispatcher) -> None:
        self._store = store
        self._dispatcher = dispatcher

    def replay_all_current_tenant(self) -> None:
        tenant_id = get_current_tenant()
        for stored in self._store.all(tenant_id=tenant_id):
            # Foundational placeholder: dispatcher expects a BaseDomainEvent.
            # In production, reconstruct events from stored metadata.
            # Here, we skip replay if types can't be resolved.
            pass

