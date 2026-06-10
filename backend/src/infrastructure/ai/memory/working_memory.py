"""Working Memory — Redis-backed per-conversation context."""

from __future__ import annotations

import json
from typing import Any, Dict, List
from uuid import UUID

try:
    import redis.asyncio as redis
except ImportError:
    redis = None  # type: ignore


class WorkingMemory:
    """Redis-backed working memory for AI conversations.

    Stores the recent conversation context that fits within the
    LLM's context window. Automatically evicts old messages when
    the token limit is approached.
    """

    PREFIX = "ai:memory"
    DEFAULT_TTL = 1800  # 30 minutes

    def __init__(self, redis_client=None) -> None:
        self._redis = redis_client

    def _key(self, tenant_id: UUID, conversation_id: UUID) -> str:
        return f"{self.PREFIX}:{tenant_id}:{conversation_id}"

    async def get_context(
        self, tenant_id: UUID, conversation_id: UUID, max_messages: int = 20
    ) -> List[Dict[str, Any]]:
        if not self._redis:
            return []
        key = self._key(tenant_id, conversation_id)
        raw = await self._redis.lrange(key, -max_messages, -1)
        return [json.loads(msg) for msg in raw]

    async def add_message(
        self, tenant_id: UUID, conversation_id: UUID, message: Dict[str, Any], max_size: int = 50
    ) -> None:
        if not self._redis:
            return
        key = self._key(tenant_id, conversation_id)
        await self._redis.rpush(key, json.dumps(message))
        await self._redis.ltrim(key, -max_size, -1)
        await self._redis.expire(key, self.DEFAULT_TTL)

    async def clear(self, tenant_id: UUID, conversation_id: UUID) -> None:
        if not self._redis:
            return
        key = self._key(tenant_id, conversation_id)
        await self._redis.delete(key)