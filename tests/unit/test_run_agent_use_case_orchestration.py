from uuid import UUID

import pytest

from backend.src.application.ai.run_agent_use_case import RunAgentUseCase
from backend.src.domains.ai.value_objects import AIInputContext
from backend.src.domains.ai.value_objects.review_state import ReviewState


class DummyAgent:
    def __init__(self, kind: str = "lesson_planning"):
        self.kind = type("K", (), {"value": kind})()
        self.risk_level = "medium"


class DummyRegistry:
    def __init__(self, agent):
        self._agent = agent

    def get(self, agent_kind: str):
        if agent_kind != self._agent.kind.value:
            raise KeyError(agent_kind)
        return self._agent


class DummyRunner:
    def __init__(self, result):
        self._result = result
        self.calls = []

    async def run_agent(self, agent, context: AIInputContext, **kwargs):
        self.calls.append({"agent": agent, "context": context, "kwargs": kwargs})
        return dict(self._result)


class DummyReviewGate:
    def get_initial_review_state(self, agent_kind: str) -> ReviewState:
        return ReviewState.PENDING


class DummyBudgetManager:
    async def check_budget(self, tenant_id: UUID, estimated_cost_cents: float):
        return {"allowed": True}


class DummyGuard:
    """Simulates the real PromptInjectionGuard behavior for testing RunAgentUseCase."""

    def __init__(self, should_reject: bool = False):
        self._should_reject = should_reject

    def detect(self, text: str):
        if self._should_reject:
            return "Potential injection detected"
        return None

    def sanitize(self, text: str) -> str:
        # When should_reject is True, sanitize returns the SAME text (cannot fix),
        # which causes RunAgentUseCase to reject
        if self._should_reject:
            return text
        return text


@pytest.mark.asyncio
async def test_run_agent_use_case_happy_path_sets_review_state():
    agent = DummyAgent("lesson_planning")
    registry = DummyRegistry(agent)
    runner = DummyRunner(result={"status": "completed", "agent_kind": "lesson_planning"})
    review_gate = DummyReviewGate()
    budget = DummyBudgetManager()
    guard = DummyGuard(should_reject=False)

    use_case = RunAgentUseCase(
        agent_registry=registry,
        agent_runner=runner,
        review_gate=review_gate,
        budget_manager=budget,
        prompt_guard=guard,
    )

    tenant_id = UUID("00000000-0000-0000-0000-00000000000a")
    user_id = UUID("00000000-0000-0000-0000-00000000a001")

    result = await use_case.execute(
        agent_kind="lesson_planning",
        tenant_id=tenant_id,
        user_id=user_id,
        domain_data={"topic": "Fractions"},
        model_override=None,
        temperature_override=None,
        max_tokens_override=None,
        conversation_id=None,
    )

    assert result["status"] == "completed"
    assert result["review_state"] == ReviewState.PENDING.value
    assert runner.calls


@pytest.mark.asyncio
async def test_run_agent_use_case_rejects_on_prompt_injection():
    agent = DummyAgent("lesson_planning")
    registry = DummyRegistry(agent)
    runner = DummyRunner(result={"status": "completed"})
    review_gate = DummyReviewGate()
    budget = DummyBudgetManager()
    guard = DummyGuard(should_reject=True)

    use_case = RunAgentUseCase(
        agent_registry=registry,
        agent_runner=runner,
        review_gate=review_gate,
        budget_manager=budget,
        prompt_guard=guard,
    )

    tenant_id = UUID("00000000-0000-0000-0000-00000000000a")
    user_id = UUID("00000000-0000-0000-0000-00000000a001")

    result = await use_case.execute(
        agent_kind="lesson_planning",
        tenant_id=tenant_id,
        user_id=user_id,
        domain_data={"notes": "bad"},
        model_override=None,
        temperature_override=None,
        max_tokens_override=None,
        conversation_id=None,
    )

    assert "error" in result
    assert result["error"] == "Input rejected"
    assert "field" in result
    assert not runner.calls