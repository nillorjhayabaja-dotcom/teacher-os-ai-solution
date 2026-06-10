"""Component tests for RAG pipeline components.

Tests verify the wiring and contract of EmbeddingService + VectorStore.
Null-path / session-free behaviour is tested here (no database required).
Integration tests with a real pgvector backend belong in:
    backend/src/tests/ai/integration/test_rag_pipeline.py
"""

import pytest
from uuid import uuid4

from backend.src.infrastructure.ai.rag.embedding_provider import EmbeddingProvider
from backend.src.infrastructure.ai.rag.embedding_service import EmbeddingService
from backend.src.infrastructure.ai.rag.fake_embedding_provider import FakeEmbeddingProvider
from backend.src.infrastructure.ai.rag.vector_store import VectorStore


class TestEmbeddingService:
    """EmbeddingService delegates to the injected provider."""

    def test_creation_defaults_to_fake_provider(self):
        service = EmbeddingService()
        assert service is not None
        assert isinstance(service.provider, FakeEmbeddingProvider)

    def test_creation_with_custom_provider(self):
        provider = FakeEmbeddingProvider(dimensions=512)
        service = EmbeddingService(provider=provider)
        assert service.provider is provider

    @pytest.mark.asyncio
    async def test_embed_returns_correct_dimension(self):
        service = EmbeddingService()
        result = await service.embed("Test text for embedding")
        assert isinstance(result, list)
        assert len(result) == 1536

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        service = EmbeddingService()
        results = await service.embed_batch(["Text 1", "Text 2"])
        assert len(results) == 2
        assert all(len(r) == 1536 for r in results)

    @pytest.mark.asyncio
    async def test_embed_consistency(self):
        service = EmbeddingService()
        result1 = await service.embed("Same text")
        result2 = await service.embed("Same text")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_provider_tracks_calls(self):
        service = EmbeddingService()
        await service.embed("hello")
        await service.embed_batch(["a", "b"])
        assert service.provider.call_count == 3


class TestFakeEmbeddingProvider:
    """FakeEmbeddingProvider implements EmbeddingProvider contract."""

    def test_satisfies_interface(self):
        provider = FakeEmbeddingProvider()
        assert isinstance(provider, EmbeddingProvider)

    @pytest.mark.asyncio
    async def test_embed_returns_zero_vector(self):
        provider = FakeEmbeddingProvider()
        result = await provider.embed("anything")
        assert result == [0.0] * 1536

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        provider = FakeEmbeddingProvider()
        results = await provider.embed_batch(["a", "b", "c"])
        assert len(results) == 3
        assert all(r == [0.0] * 1536 for r in results)


class TestVectorStore:
    """VectorStore safe no-op behaviour when session is None."""

    def test_creation(self):
        provider = FakeEmbeddingProvider()
        store = VectorStore(session=None, embedding_fn=provider)
        assert store is not None

    @pytest.mark.asyncio
    async def test_search_returns_list_without_session(self):
        provider = FakeEmbeddingProvider()
        store = VectorStore(session=None, embedding_fn=provider)
        results = await store.search("test query", tenant_id=uuid4(), top_k=5)
        assert isinstance(results, list)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_does_not_embed_without_session(self):
        provider = FakeEmbeddingProvider()
        store = VectorStore(session=None, embedding_fn=provider)
        await store.search("test", tenant_id=uuid4(), top_k=3)
        assert provider.call_count == 0

    @pytest.mark.asyncio
    async def test_search_empty_db(self):
        provider = FakeEmbeddingProvider()
        store = VectorStore(session=None, embedding_fn=provider)
        results = await store.search("anything", tenant_id=uuid4())
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_upsert_chunks_count(self):
        provider = FakeEmbeddingProvider()
        store = VectorStore(session=None, embedding_fn=provider)
        chunks = [
            {"content": "MELC: Fractions", "knowledge_type": "melc", "token_count": 10},
            {"content": "MELC: Addition", "knowledge_type": "melc", "token_count": 8},
        ]
        count = await store.upsert_chunks(chunks, tenant_id=uuid4())
        assert count == 0

    @pytest.mark.asyncio
    async def test_delete_chunks_returns_zero_without_session(self):
        provider = FakeEmbeddingProvider()
        store = VectorStore(session=None, embedding_fn=provider)
        count = await store.delete_chunks(uuid4(), source_type="melc")
        assert count == 0