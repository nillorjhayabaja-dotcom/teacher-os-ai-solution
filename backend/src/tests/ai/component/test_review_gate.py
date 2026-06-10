"""Component tests for AIReviewGate."""

import pytest
from uuid import uuid4

from backend.src.domains.ai.services.review_gate import AIReviewGate
from backend.src.domains.ai.value_objects import ReviewState
from backend.src.infrastructure.ai.agent_registry import AgentRegistry
from backend.src.domains.ai.agents.student_risk_agent import StudentRiskAgent
from backend.src.domains.ai.agents.lesson_planning_agent import LessonPlanningAgent
from backend.src.domains.ai.agents.communication_agent import CommunicationAgent


@pytest.fixture
def registry():
    return AgentRegistry()


@pytest.fixture
def review_gate(registry):
    return AIReviewGate(agent_registry=registry)


class TestAIReviewGate:
    def test_auto_approve_low_risk(self, review_gate):
        result = review_gate.should_auto_approve("student_risk")
        assert result is True

    def test_auto_approve_medium_risk(self, review_gate):
        result = review_gate.should_auto_approve("lesson_planning")
        assert result is False

    def test_auto_approve_high_risk(self, review_gate):
        result = review_gate.should_auto_approve("communication")
        assert result is False

    def test_get_initial_review_state_low_risk(self, review_gate):
        state = review_gate.get_initial_review_state("student_risk")
        assert state == ReviewState.AUTO_APPROVED

    def test_get_initial_review_state_medium_risk(self, review_gate):
        state = review_gate.get_initial_review_state("lesson_planning")
        assert state == ReviewState.PENDING

    def test_get_initial_review_state_high_risk(self, review_gate):
        state = review_gate.get_initial_review_state("communication")
        assert state == ReviewState.PENDING

    def test_get_reviewers_medium_risk(self, review_gate):
        reviewers = review_gate.get_reviewers("lesson_planning", uuid4())
        assert len(reviewers) == 1
        assert reviewers[0]["role"] == "teacher"

    def test_get_reviewers_high_risk(self, review_gate):
        reviewers = review_gate.get_reviewers("communication", uuid4())
        assert len(reviewers) == 2
        roles = [r["role"] for r in reviewers]
        assert "teacher" in roles
        assert "principal" in roles

    def test_get_reviewers_low_risk(self, review_gate):
        reviewers = review_gate.get_reviewers("student_risk", uuid4())
        assert len(reviewers) == 0


class TestAgentRegistry:
    def test_registry_has_seven_agents(self):
        registry = AgentRegistry()
        agents = registry.list_agents()
        assert len(agents) >= 7

    def test_get_agent_by_kind(self):
        registry = AgentRegistry()
        agent = registry.get("lesson_planning")
        assert agent is not None
        assert agent.kind.value == "lesson_planning"

    def test_get_or_none_returns_none(self):
        registry = AgentRegistry()
        assert registry.get_or_none("nonexistent") is None

    def test_get_or_none_returns_agent(self):
        registry = AgentRegistry()
        agent = registry.get_or_none("assessment")
        assert agent is not None