"""Abstract base class for all AI agents."""

from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..value_objects import (
    AIInputContext,
    AgentKind,
    ModelConfig,
)


class BaseAgent(abc.ABC):
    """Abstract base class for all AI agents.

    Every concrete agent implements domain-specific logic while the
    infrastructure layer handles LLM communication, cost tracking,
    and observability.
    """

    # Subclass must define these
    kind: AgentKind
    name: str
    description: str
    default_model: ModelConfig
    required_tools: List[str] = []
    optional_tools: List[str] = []
    max_input_tokens: int = 8000
    supports_streaming: bool = True
    supports_conversation: bool = False
    risk_level: str = "medium"  # "low" | "medium" | "high"

    @abc.abstractmethod
    async def build_messages(
        self,
        context: AIInputContext,
        prompt_version_id: UUID,
    ) -> List[Dict[str, str]]:
        """Assemble the message array for the LLM."""
        ...

    @abc.abstractmethod
    async def parse_response(
        self,
        raw_response: str,
        context: AIInputContext,
    ) -> Dict[str, Any]:
        """Parse and validate the LLM response into structured output."""
        ...

    @abc.abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """Return the JSON Schema for this agent's output."""
        ...

    async def validate_input(self, context: AIInputContext) -> None:
        """Pre-flight input validation."""
        pass

    async def post_process(
        self,
        output: Dict[str, Any],
        context: AIInputContext,
    ) -> Dict[str, Any]:
        """Post-process the parsed output before persistence."""
        return output

    async def get_rag_query(self, context: AIInputContext) -> Optional[str]:
        """Return a query string for RAG retrieval. Returns None to skip RAG."""
        return None

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Return OpenAI-compatible tool/function schemas for this agent."""
        return []