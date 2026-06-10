from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from .workflow_definition import WorkflowDefinition


@dataclass(frozen=True)
class WorkflowEngineResult:
    next_state: str
    metadata: Dict[str, Any] | None = None


class WorkflowEngine:
    """Generic workflow engine operating over a transition map."""

    def __init__(self, transitions: Mapping[str, Mapping[str, str]]) -> None:
        self._transitions = transitions

    @classmethod
    def from_definition(cls, definition: WorkflowDefinition) -> "WorkflowEngine":
        # Current WorkflowDefinition is a placeholder; keep compatibility.
        transitions: Dict[str, Dict[str, str]] = getattr(definition, "transitions", {}) or {}
        return cls(transitions=transitions)

    def next_state(self, cur_state: str, event: str) -> WorkflowEngineResult:
        try:
            next_state = self._transitions[cur_state][event]
            return WorkflowEngineResult(next_state=next_state)
        except KeyError as e:
            raise ValueError(f"Invalid transition {cur_state}->{event}") from e

