"""AI Generation Celery tasks — async AI agent execution."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from backend.src.infrastructure.message_queue.celery_app import celery_app


@celery_app.task(bind=True, queue="ai_generation", max_retries=3, default_retry_delay=30)
def run_ai_agent_task(self, *, agent_kind: str, tenant_id: str, user_id: str, domain_data: Dict[str, Any]):
    """Execute an AI agent asynchronously via Celery.

    This task is dispatched when a user triggers an AI generation.
    The result is stored and a WebSocket notification is sent on completion.
    """
    import asyncio

    async def _execute():
        from backend.src.infrastructure.ai.agent_registry import AgentRegistry
        from backend.src.infrastructure.ai.providers.fake_provider import FakeLLMProvider
        from backend.src.infrastructure.ai.prompts.prompt_registry import PromptRegistry
        from backend.src.infrastructure.ai.cost.budget_manager import BudgetManager
        from backend.src.infrastructure.ai.security.prompt_guard import PromptInjectionGuard
        from backend.src.domains.ai.services.agent_runner import AgentRunner
        from backend.src.domains.ai.services.review_gate import AIReviewGate
        from backend.src.domains.ai.services.cost_calculator import CostCalculator
        from backend.src.application.ai.run_agent_use_case import RunAgentUseCase

        registry = AgentRegistry()
        llm = FakeLLMProvider()
        prompts = PromptRegistry()
        runner = AgentRunner(llm_provider=llm, prompt_registry=prompts, cost_calculator=CostCalculator())
        review_gate = AIReviewGate(agent_registry=registry)
        budget = BudgetManager()
        guard = PromptInjectionGuard()

        use_case = RunAgentUseCase(
            agent_registry=registry,
            agent_runner=runner,
            review_gate=review_gate,
            budget_manager=budget,
            prompt_guard=guard,
        )

        return await use_case.execute(
            agent_kind=agent_kind,
            tenant_id=UUID(tenant_id),
            user_id=UUID(user_id),
            domain_data=domain_data,
        )

    try:
        result = asyncio.run(_execute())
        return result
    except Exception as exc:
        self.retry(exc=exc)