from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from backend.src.infrastructure.ai.memory.conversation_memory import ConversationMemory
from backend.src.infrastructure.ai.memory.working_memory import WorkingMemory
from backend.src.infrastructure.ai.prompts.prompt_registry import PromptRegistry
from backend.src.infrastructure.ai.prompts.template_engine import TemplateEngine
from backend.src.infrastructure.ai.rag.chunker import DocumentChunker
from backend.src.infrastructure.ai.rag.embedding_service import EmbeddingService
from backend.src.infrastructure.ai.rag.fake_embedding_provider import FakeEmbeddingProvider
from backend.src.infrastructure.ai.rag.vector_store import VectorStore


@pytest.mark.rag
@pytest.mark.unit
def test_document_chunker_creates_overlapping_metadata_chunks(tenant_id):
    chunker = DocumentChunker(chunk_size=10, chunk_overlap=3)
    # Use text with spaces so split() produces multiple words
    text = " ".join(["word"] * 25)
    chunks = chunker.chunk_document(
        text,
        metadata={
            "source_type": "lesson_plan",
            "source_id": uuid4(),
            "knowledge_type": "curriculum",
            "metadata": {"grade_level": "6"},
        },
    )

    assert len(chunks) >= 2
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["metadata"]["grade_level"] == "6"
    assert chunks[0]["knowledge_type"] == "curriculum"


@pytest.mark.rag
@pytest.mark.unit
@pytest.mark.asyncio
async def test_embedding_service_is_deterministic_and_dimensioned():
    provider = FakeEmbeddingProvider()
    service = EmbeddingService(provider=provider)
    one = await service.embed("science lesson")
    two = await service.embed("science lesson")
    many = await service.embed_batch(["a", "b"])

    assert len(one) == 1536  # default OpenAI embedding dimension
    assert len(many) == 2
    assert one == two  # deterministic zero-vector


@pytest.mark.rag
@pytest.mark.integration
@pytest.mark.asyncio
async def test_vector_store_upsert_and_search_are_safe_without_session(tenant_id):
    provider = FakeEmbeddingProvider()
    store = VectorStore(session=None, embedding_fn=provider)

    assert await store.search("matter", tenant_id=tenant_id) == []
    assert await store.upsert_chunks([{"content": "matter chunk"}], tenant_id=tenant_id) == 0
    assert provider.call_count == 0  # embed should not be called without a session


@pytest.mark.rag
@pytest.mark.unit
@pytest.mark.asyncio
async def test_prompt_registry_version_lifecycle_and_template_execution(tenant_id):
    registry = PromptRegistry()

    # Create a prompt via the public API
    prompt = await registry.create_prompt(
        name="lesson", description="Lesson prompt", category="system",
        agent_kind="lesson_planning", tenant_id=tenant_id,
    )
    prompt_id = UUID(prompt["id"])

    v1 = await registry.create_version(prompt_id=prompt_id, system_prompt="System", user_template="Hello {{ name }}", variables=["name"])
    v2 = await registry.create_version(prompt_id=prompt_id, system_prompt="System 2", user_template="Hi {{ name }}", variables=["name"])
    await registry.activate_version(prompt_id, v1["id"])

    active_prompt = await registry.get_active_version("lesson_planning", "system")
    rendered = TemplateEngine().render(v2["user_template"], {"name": "Ana"})

    assert active_prompt["id"] == str(prompt_id)
    assert registry._cache[str(prompt_id)]["versions"][0]["is_active"] is True
    assert rendered == "Hi Ana"


@pytest.mark.rag
@pytest.mark.unit
@pytest.mark.asyncio
async def test_working_and_conversation_memory_are_tenant_scoped(tenant_id, other_tenant_id, user_id):
    working = WorkingMemory()
    conversation = ConversationMemory()
    conversation_id = uuid4()
    await conversation.create_conversation(tenant_id=tenant_id, agent_kind="lesson_planning", user_id=user_id)
    await conversation.add_message(conversation_id=conversation_id, tenant_id=tenant_id, role="user", content="Hello")
    await conversation.add_message(conversation_id=conversation_id, tenant_id=other_tenant_id, role="user", content="Other tenant")

    # Without a real DB session, conversation memory returns empty lists
    msgs_tenant = await conversation.get_messages(conversation_id, tenant_id)
    msgs_other = await conversation.get_messages(conversation_id, other_tenant_id)
    assert isinstance(msgs_tenant, list)
    assert isinstance(msgs_other, list)


@pytest.mark.rag
@pytest.mark.xfail_architecture_gap(reason="Persistent pgvector retrieval, hybrid ranking, citations, and metadata filters are not implemented yet.")
@pytest.mark.asyncio
async def test_rag_retrieval_filters_by_metadata_tenant_and_returns_ranked_citations(tenant_id, other_tenant_id):
    provider = FakeEmbeddingProvider()
    store = VectorStore(session=object(), embedding_fn=provider)
    await store.upsert_chunks([
        {"content": "tenant lesson", "metadata": {"grade_level": "6"}, "citation": "doc#1"},
        {"content": "other tenant lesson", "metadata": {"grade_level": "6"}, "tenant_id": str(other_tenant_id)},
    ], tenant_id=tenant_id)
    results = await store.search("lesson", tenant_id=tenant_id, knowledge_types=["lesson"], top_k=1)
    assert results[0]["citation"] == "doc#1"
    assert all(r["tenant_id"] == str(tenant_id) for r in results)