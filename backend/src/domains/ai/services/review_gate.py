"""AI Review Gate — determines human-in-the-loop review requirements."""

from __future__ import annotations

from typing import Dict, List
from uuid import UUID

from ..agents.base_agent import BaseAgent
from ..value_objects import ReviewState


class AIReviewGate:
    """Determines whether an AI output requires human review.

    Risk-based auto-approval policy:
    - LOW risk:    Auto-approve
    - MEDIUM risk: Require teacher review
    - HIGH risk:   Require teacher + principal review
    """

    AUTO_APPROVE_RISK_LEVELS = {"low"}
    TEACHER_REVIEW_RISK_LEVELS = {"medium"}
    MULTI_REVIEW_RISK_LEVELS = {"high"}

    def __init__(self, agent_registry) -> None:
        self._agent_registry = agent_registry

    def should_auto_approve(self, agent_kind: str) -> bool:
        agent = self._agent_registry.get(agent_kind)
        return agent.risk_level in self.AUTO_APPROVE_RISK_LEVELS

    def get_initial_review_state(self, agent_kind: str) -> ReviewState:
        if self.should_auto_approve(agent_kind):
            return ReviewState.AUTO_APPROVED
        return ReviewState.PENDING

    def get_reviewers(self, agent_kind: str, tenant_id: UUID) -> List[Dict]:
        agent = self._agent_registry.get(agent_kind)
        if agent.risk_level in self.MULTI_REVIEW_RISK_LEVELS:
            return [
                {"role": "teacher", "required": True},
                {"role": "principal", "required": True},
            ]
        elif agent.risk_level in self.TEACHER_REVIEW_RISK_LEVELS:
            return [{"role": "teacher", "required": True}]
        return []