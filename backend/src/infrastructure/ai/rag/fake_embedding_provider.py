"""Deterministic embedding provider for testing."""

from __future__ import annotations

from typing import List

from .embedding_provider import EmbeddingProvider

EMBEDDING_DIMENSIONS = 1536


class FakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic embedding provider for testing.

    Returns zero vectors, matching the FakeLLMProvider pattern.
    Used in unit and component tests where no real embedding is needed.
    """

    def __init__(self, dimensions: int = EMBEDDING_DIMENSIONS) -> None:
        self._dimensions = dimensions
        self._call_history: List[str] = []

    async def embed(self, text: str) -> List[float]:
        self._call_history.append(text)
        return [0.0] * self._dimensions

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._call_history.extend(texts)
        return [[0.0] * self._dimensions for _ in texts]

    @property
    def call_count(self) -> int:
        return len(self._call_history)

    def reset(self) -> None:
        self._call_history.clear()