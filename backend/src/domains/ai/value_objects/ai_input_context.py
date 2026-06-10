"""AI input context value object."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
from uuid import UUID


@dataclass(frozen=True)
class AIInputContext:
    """Structured input context assembled for an agent run."""

    tenant_id: UUID
    agent_kind: str
    user_id: UUID
    domain_data: Dict[str, Any]
    conversation_history: List[Dict] = field(default_factory=list)
    rag_context: List[Dict] = field(default_factory=list)
    additional_context: Dict[str, Any] = field(default_factory=dict)