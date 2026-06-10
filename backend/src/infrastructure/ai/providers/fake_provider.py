"""Fake LLM Provider for testing."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List

from .base_provider import AIProvider


class FakeLLMProvider(AIProvider):
    """Deterministic LLM provider for testing."""

    def __init__(self) -> None:
        self._responses: Dict[str, str] = {}
        self._call_history: List[Dict[str, Any]] = []

    def program_response(self, agent_kind: str, response: str) -> None:
        self._responses[agent_kind] = response

    async def chat(self, messages: List[Dict], model_config: Any) -> str:
        self._call_history.append({"messages": messages, "model": model_config.model_name})
        agent_kind = messages[0].get("metadata", {}).get("agent_kind", "default")
        return self._responses.get(agent_kind, '{"error": "no programmed response"}')

    async def chat_stream(self, messages: List[Dict], model_config: Any) -> AsyncIterator[str]:
        response = await self.chat(messages, model_config)
        yield response

    @property
    def call_count(self) -> int:
        return len(self._call_history)

    @property
    def last_call(self) -> Dict[str, Any]:
        return self._call_history[-1] if self._call_history else {}

    def reset(self) -> None:
        self._responses.clear()
        self._call_history.clear()