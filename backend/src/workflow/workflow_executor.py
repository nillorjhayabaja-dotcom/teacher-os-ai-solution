from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from backend.src.core.tenant_context import get_current_tenant

from .workflow_engine import WorkflowEngine
from .workflow_history import WorkflowHistory, WorkflowHistoryEntry


@dataclass(frozen=True)
class WorkflowExecution:
    workflow_id: str
    tenant_id: str
    from_state: str
    event: str
    to_state: str
    metadata: Dict[str, Any] | None = None


class WorkflowExecutor:
    """Executes workflow transitions and records history.

    Foundational placeholder: emits no events yet (that will be wired via
    event store/bus in a later step).
    """

    def __init__(self, engine: WorkflowEngine, *, history: Optional[WorkflowHistory] = None) -> None:
        self._engine = engine
        self._history = history or WorkflowHistory()

    def execute(
        self,
        *,
        workflow_id: str,
        current_state: str,
        event: str,
        actor_id: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        tenant_id = get_current_tenant()
        result = self._engine.next_state(current_state, event)

        entry = WorkflowHistoryEntry(
            workflow_id=workflow_id,
            from_state=current_state,
            event=event,
            to_state=result.next_state,
            actor_id=actor_id,
            metadata=metadata,
            created_at="",
        )
        self._history.record(entry)

        return WorkflowExecution(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            from_state=current_state,
            event=event,
            to_state=result.next_state,
            metadata=metadata,
        )

