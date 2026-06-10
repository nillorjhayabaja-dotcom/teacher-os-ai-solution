"""Abstract embedding provider interface — mirrors AIProvider pattern."""

from __future__ import annotations

import abc
from typing import List


class EmbeddingProvider(abc.ABC):
    """Abstract interface for embedding providers.

    Follows the same pattern as AIProvider (base_provider.py):
    concrete implementations (OpenAI, Fake) are injected via DI.
    """

    @abc.abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate an embedding vector for the given text."""
        ...

    @abc.abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of texts."""
        ...