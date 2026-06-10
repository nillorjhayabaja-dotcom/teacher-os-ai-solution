"""Unit tests for Tool Registry."""

from uuid import uuid4

import pytest
from backend.src.infrastructure.ai.tools.tool_registry import ToolRegistry


class TestToolRegistry:
    def setup_method(self):
        self.registry = ToolRegistry()

    def test_register_defaults(self):
        tools = self.registry.list_all()
        assert len(tools) == 12

    def test_get_existing_tool(self):
        tool = self.registry.get("curriculum_search")
        assert tool is not None
        assert tool.name == "curriculum_search"

    def test_get_nonexistent_tool(self):
        assert self.registry.get("nonexistent") is None

    def test_get_or_raise(self):
        with pytest.raises(KeyError, match="Tool not found"):
            self.registry.get_or_raise("nonexistent")

    def test_get_schemas_for_agent(self):
        schemas = self.registry.get_schemas_for_agent(["curriculum_search", "melc_lookup"])
        assert len(schemas) == 2
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "curriculum_search"

    def test_get_schemas_skips_missing(self):
        schemas = self.registry.get_schemas_for_agent(["curriculum_search", "nonexistent"])
        assert len(schemas) == 1

    def test_to_openai_tool(self):
        tool = self.registry.get("student_search")
        openai_tool = tool.to_openai_tool()
        assert openai_tool["type"] == "function"
        assert "parameters" in openai_tool["function"]

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        tool = self.registry.get("transmutation_lookup")
        assert tool is not None
        result = await tool.execute(
            {"initial_grade": 80},
            tenant_id=uuid4(),
            user_id=uuid4(),
            run_id=uuid4(),
        )
        assert "initial_grade" in result
        assert "transmuted_grade" in result
