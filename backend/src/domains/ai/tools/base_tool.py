"""Abstract base class for AI tools."""

from __future__ import annotations

import abc
from typing import Any, Dict
from uuid import UUID


class AITool(abc.ABC):
    """Interface for tools that AI agents can invoke.

    Tools are tenant-scoped functions that agents call to interact
    with the TeacherOS platform during execution.
    """

    name: str
    description: str
    requires_tenant: bool = True
    has_side_effects: bool = False

    @abc.abstractmethod
    async def execute(
        self,
        arguments: Dict[str, Any],
        *,
        tenant_id: UUID,
        user_id: UUID,
        run_id: UUID,
    ) -> Dict[str, Any]:
        """Execute the tool with the given arguments."""
        ...

    @abc.abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return OpenAI-compatible function schema."""
        ...

    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_schema(),
            },
        }