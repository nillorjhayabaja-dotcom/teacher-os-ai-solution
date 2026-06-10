from __future__ import annotations

import time

import pytest

from backend.src.domains.ai.services.agent_runner import AgentRunner
from backend.src.domains.ai.value_objects import AIInputContext, AgentKind
from backend.src.infrastructure.ai.agent_registry import AgentRegistry
from backend.src.infrastructure.ai.prompts.prompt_registry import PromptRegistry
from backend.src.infrastructure.ai.providers.fake_provider import FakeLLMProvider
from backend.src.infrastructure.ai.rag.embedding_service import EmbeddingService


@pytest.mark.performance
@pytest.mark.asyncio
async def test_rag_embedding_latency_smoke():
    service = EmbeddingService()
    start = time.perf_counter()
    vectors = await service.embed_batch([f"document {i}" for i in range(100)])
    elapsed = time.perf_counter() - start
    assert len(vectors) == 100
    assert elapsed < 5.0  # Generous timeout for fallback embedding


@pytest.mark.performance
@pytest.mark.asyncio
async def test_agent_execution_latency_smoke(tenant_id, user_id, sample_domain_data):
    runner = AgentRunner(llm_provider=FakeLLMProvider(), prompt_registry=PromptRegistry())
    agent = AgentRegistry().get("lesson_planning")
    context = AIInputContext(tenant_id=tenant_id, user_id=user_id, agent_kind=AgentKind.LESSON_PLANNING, domain_data=sample_domain_data)

    start = time.perf_counter()
    result = await runner.run_agent(agent, context)
    elapsed = time.perf_counter() - start

    assert result["status"] == "completed"
    assert elapsed < 1.0


@pytest.mark.performance
@pytest.mark.xfail_architecture_gap(reason="Database query counting/cache hit metrics require repository and cache implementations not present yet.")
def test_student_search_grade_computation_form_generation_query_and_cache_benchmarks():
    assert False, "Repository query counters and cache metrics must be implemented before this benchmark can pass."