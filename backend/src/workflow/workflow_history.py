from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class WorkflowHistoryEntry:
    workflow_id: str
    from_state: str
    event: str
    to_state: str
    actor_id: Optional[str] = None
    metadata: Dict[str, Any] | None = None
    created_at: str = ""


class WorkflowHistory:
    """In-memory workflow history.

    Foundational placeholder. Later versions can persist this via the event
    store.
    """

    def __init__(self) -> None:
        self._entries: List[WorkflowHistoryEntry] = []

    def record(self, entry: WorkflowHistoryEntry) -> None:
        created_at = entry.created_at or datetime.now(timezone.utc).isoformat()
        self._entries.append(
            WorkflowHistoryEntry(
                workflow_id=entry.workflow_id,
                from_state=entry.from_state,
                event=entry.event,
                to_state=entry.to_state,
                actor_id=entry.actor_id,
                metadata=entry.metadata,
                created_at=created_at,
            )
        )

    def all_for_workflow(self, workflow_id: str) -> List[WorkflowHistoryEntry]:
        return [e for e in self._entries if e.workflow_id == workflow_id]

