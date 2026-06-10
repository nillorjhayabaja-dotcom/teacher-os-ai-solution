"""Abstract AI Provider interface."""

from __future__ import annotations

import abc
from typing import Any, AsyncIterator, Dict, List


class AIProvider(abc.ABC):
    """Abstract interface for LLM providers."""

    @abc.abstractmethod
    async def chat(self, messages: List[Dict[str, str]], model_config: Any) -> str:
        """Send a chat completion request and return the response text."""
        ...

    @abc.abstractmethod
    async def chat_stream(self, messages: List[Dict[str, str]], model_config: Any) -> AsyncIterator[str]:
        """Stream a chat completion response."""
        ...