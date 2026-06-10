"""OpenAI embedding provider implementation."""

from __future__ import annotations

import logging
from typing import List

from .embedding_provider import EmbeddingProvider

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Generates embeddings via the OpenAI API.

    Uses the native batch API for ``embed_batch`` to minimize round-trips.
    Requires a valid OpenAI API key and the ``openai`` package.
    """

    DEFAULT_MODEL = "text-embedding-3-small"
    DEFAULT_DIMENSIONS = 1536
    MAX_BATCH_SIZE = 100

    def __init__(self, api_key: str, *, model: str | None = None) -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self._api_key = api_key
        self._model = model or self.DEFAULT_MODEL

    async def embed(self, text: str) -> List[float]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self._api_key)
        response = await client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self._api_key)
        response = await client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in response.data]