"""AI domain events — emitted by the AI bounded context."""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from backend.src.events.base_domain_event import BaseDomainEvent


class AIRunStarted(BaseDomainEvent):
    """Emitted when an agent run begins execution."""
    run_id: UUID
    agent_kind: str
    tenant_id: UUID
    user_id: UUID


class AIRunCompleted(BaseDomainEvent):
    """Emitted when an agent run finishes successfully."""
    run_id: UUID
    agent_kind: str
    tenant_id: UUID
    user_id: UUID
    output_id: UUID
    token_usage: Dict[str, int]
    cost_cents: float
    latency_ms: int


class AIRunFailed(BaseDomainEvent):
    """Emitted when an agent run fails."""
    run_id: UUID
    agent_kind: str
    tenant_id: UUID
    user_id: UUID
    error_type: str
    error_message: str
    retry_count: int


class AIOutputGenerated(BaseDomainEvent):
    """Emitted when a new AI output is created."""
    output_id: UUID
    run_id: UUID
    agent_kind: str
    tenant_id: UUID
    superseded_output_id: Optional[UUID]


class AIOutputReviewed(BaseDomainEvent):
    """Emitted when a human reviews an AI output."""
    output_id: UUID
    tenant_id: UUID
    reviewer_id: UUID
    review_state: str
    feedback_id: Optional[UUID]


class AIFeedbackSubmitted(BaseDomainEvent):
    """Emitted when feedback is submitted on an AI output."""
    feedback_id: UUID
    output_id: UUID
    tenant_id: UUID
    reviewer_id: UUID
    rating: int


class AIBudgetAlert(BaseDomainEvent):
    """Emitted when a tenant approaches or exceeds budget."""
    tenant_id: UUID
    alert_level: str
    current_spend_cents: float
    budget_limit_cents: float
    period: str


class AIToolExecuted(BaseDomainEvent):
    """Emitted when an agent executes a tool."""
    execution_id: UUID
    run_id: UUID
    tool_name: str
    tenant_id: UUID
    success: bool
    latency_ms: int