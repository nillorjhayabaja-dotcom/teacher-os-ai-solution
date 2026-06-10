from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class WorkflowTransition:
    """Transition definition from one state to another triggered by an event."""

    from_state: str
    event: str
    to_state: str
    metadata: Dict[str, Any] | None = None
    actor_id: Optional[str] = None

