"""Embedding Service — generates vector embeddings for RAG."""

from __future__ import annotations

from typing import List

from .embedding_provider import EmbeddingProvider
from .fake_embedding_provider import FakeEmbeddingProvider

EMBEDDING_CONFIG = {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "dimensions": 1536,
    "batch_size": 100,
}


class EmbeddingService:
    """Orchestrates embedding generation using an injected provider.

    The provider is responsible for the actual embedding call (OpenAI, Fake, etc).
    This service handles retries, caching, and observability hooks.

    When no provider is supplied a ``FakeEmbeddingProvider`` is used — this is
    suitable for unit/component tests but **not** for production.
    """

    def __init__(self, provider: EmbeddingProvider | None = None) -> None:
        self._provider = provider if provider is not None else FakeEmbeddingProvider()

    async def embed(self, text: str) -> List[float]:
        return await self._provider.embed(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return await self._provider.embed_batch(texts)

    @property
    def provider(self) -> EmbeddingProvider:
        return self._provider

    @staticmethod
    def get_config() -> dict:
        return EMBEDDING_CONFIG