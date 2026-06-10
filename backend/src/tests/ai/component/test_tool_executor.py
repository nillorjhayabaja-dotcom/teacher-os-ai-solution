"""Component tests for tool execution via ToolRegistry."""

import pytest
from uuid import uuid4

from backend.src.infrastructure.ai.tools.tool_registry import ToolRegistry
from backend.src.domains.ai.value_objects import AgentKind


class TestToolRegistry:
    def test_registry_has_all_tools(self):
        registry = ToolRegistry()
        tools = registry.list_all()
        assert len(tools) >= 12

    def test_get_curriculum_search(self):
        registry = ToolRegistry()
        tool = registry.get("curriculum_search")
        assert tool is not None
        assert tool.name == "curriculum_search"
        assert not tool.has_side_effects

    def test_get_melc_lookup(self):
        registry = ToolRegistry()
        tool = registry.get("melc_lookup")
        assert tool is not None
        assert "melc" in tool.description.lower()

    def test_get_notification_sender(self):
        registry = ToolRegistry()
        tool = registry.get("notification_sender")
        assert tool is not None
        assert tool.has_side_effects

    def test_get_or_raise_success(self):
        registry = ToolRegistry()
        tool = registry.get_or_raise("student_search")
        assert tool.name == "student_search"

    def test_get_or_raise_failure(self):
        registry = ToolRegistry()
        with pytest.raises(KeyError):
            registry.get_or_raise("nonexistent_tool")

    def test_get_schemas_for_agent(self):
        registry = ToolRegistry()
        schemas = registry.get_schemas_for_agent(["curriculum_search", "melc_lookup"])
        assert len(schemas) == 2
        for s in schemas:
            assert s["type"] == "function"
            assert "function" in s

    def test_register_override(self):
        registry = ToolRegistry()
        original = registry.get("curriculum_search")
        assert original is not None

        class MockTool:
            name = "curriculum_search"
            description = "Mock"
            requires_tenant = False
            has_side_effects = False

            async def execute(self, arguments, *, tenant_id, user_id, run_id):
                return {"mocked": True}

            def get_schema(self):
                return {"type": "object", "properties": {}}

            def to_openai_tool(self):
                return {"type": "function", "function": {"name": self.name, "description": self.description, "parameters": self.get_schema()}}

        registry.register(MockTool())
        assert registry.get("curriculum_search").description == "Mock"


class TestCurriculumSearchTool:
    @pytest.mark.asyncio
    async def test_execute_returns_query(self):
        registry = ToolRegistry()
        tool = registry.get("curriculum_search")
        result = await tool.execute(
            {"subject": "Mathematics", "grade_level": "Grade 3"},
            tenant_id=uuid4(), user_id=uuid4(), run_id=uuid4(),
        )
        assert "query" in result
        assert result["query"]["subject"] == "Mathematics"

    @pytest.mark.asyncio
    async def test_get_schema(self):
        registry = ToolRegistry()
        tool = registry.get("curriculum_search")
        schema = tool.get_schema()
        assert schema["type"] == "object"
        assert "subject" in schema["properties"]


class TestMelcLookupTool:
    @pytest.mark.asyncio
    async def test_execute_with_code(self):
        registry = ToolRegistry()
        tool = registry.get("melc_lookup")
        result = await tool.execute(
            {"melc_code": "M3NS-Ia-1"},
            tenant_id=uuid4(), user_id=uuid4(), run_id=uuid4(),
        )
        assert result["query"]["melc_code"] == "M3NS-Ia-1"

    @pytest.mark.asyncio
    async def test_schema_requires_melc_code(self):
        registry = ToolRegistry()
        tool = registry.get("melc_lookup")
        schema = tool.get_schema()
        assert "melc_code" in schema["required"]


class TestNotificationSenderTool:
    @pytest.mark.asyncio
    async def test_execute_returns_queued(self):
        registry = ToolRegistry()
        tool = registry.get("notification_sender")
        result = await tool.execute(
            {"recipient_id": "user-123", "channel": "email", "body": "Hello"},
            tenant_id=uuid4(), user_id=uuid4(), run_id=uuid4(),
        )
        assert "sent" in result

    @pytest.mark.asyncio
    async def test_has_side_effects(self):
        registry = ToolRegistry()
        tool = registry.get("notification_sender")
        assert tool.has_side_effects


class TestToolExecutionPipeline:
    @pytest.mark.asyncio
    async def test_execute_with_tenant_context(self):
        registry = ToolRegistry()
        tool = registry.get("student_search")
        tenant_id = uuid4()
        result = await tool.execute(
            {"name": "Juan"},
            tenant_id=tenant_id, user_id=uuid4(), run_id=uuid4(),
        )
        assert result["query"]["name"] == "Juan"

    @pytest.mark.asyncio
    async def test_execute_with_empty_args(self):
        registry = ToolRegistry()
        tool = registry.get("attendance_analyzer")
        result = await tool.execute(
            {},
            tenant_id=uuid4(), user_id=uuid4(), run_id=uuid4(),
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_all_tools_have_schema(self):
        registry = ToolRegistry()
        for tool in registry.list_all():
            schema = tool.get_schema()
            assert schema["type"] == "object", f"{tool.name} missing schema"