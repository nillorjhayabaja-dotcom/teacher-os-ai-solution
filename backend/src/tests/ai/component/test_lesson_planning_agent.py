"""Component tests for LessonPlanningAgent with FakeLLMProvider."""

import pytest
import json
from uuid import uuid4

from backend.src.domains.ai.agents.lesson_planning_agent import LessonPlanningAgent
from backend.src.domains.ai.value_objects import AIInputContext
from backend.src.infrastructure.ai.providers.fake_provider import FakeLLMProvider


@pytest.fixture
def agent():
    return LessonPlanningAgent()


@pytest.fixture
def llm():
    return FakeLLMProvider()


@pytest.fixture
def sample_context():
    return AIInputContext(
        tenant_id=uuid4(),
        agent_kind="lesson_planning",
        user_id=uuid4(),
        domain_data={
            "grade_level": "Grade 3",
            "subject": "Mathematics",
            "topic": "Introduction to Fractions",
            "duration_minutes": 60,
        },
    )


class TestLessonPlanningAgentBuildMessages:
    @pytest.mark.asyncio
    async def test_build_messages_returns_list(self, agent, sample_context):
        messages = await agent.build_messages(sample_context, uuid4())
        assert isinstance(messages, list)
        assert len(messages) >= 1

    @pytest.mark.asyncio
    async def test_build_messages_has_system_prompt(self, agent, sample_context):
        messages = await agent.build_messages(sample_context, uuid4())
        assert messages[0]["role"] == "system"
        assert "lesson planning" in messages[0]["content"].lower()

    @pytest.mark.asyncio
    async def test_build_messages_has_user_prompt(self, agent, sample_context):
        messages = await agent.build_messages(sample_context, uuid4())
        assert messages[-1]["role"] == "user"
        assert "Grade 3" in messages[-1]["content"]

    @pytest.mark.asyncio
    async def test_build_messages_includes_rag_context(self, agent, sample_context):
        ctx = AIInputContext(
            tenant_id=sample_context.tenant_id,
            agent_kind=sample_context.agent_kind,
            user_id=sample_context.user_id,
            domain_data=sample_context.domain_data,
            rag_context=[{"content": "MELC: Demonstrate understanding of fractions"}],
        )
        messages = await agent.build_messages(ctx, uuid4())
        user_msg = messages[-1]["content"]
        assert "MELC" in user_msg or "Reference" in user_msg

    @pytest.mark.asyncio
    async def test_build_messages_with_conversation_history(self, agent, sample_context):
        ctx = AIInputContext(
            tenant_id=sample_context.tenant_id,
            agent_kind=sample_context.agent_kind,
            user_id=sample_context.user_id,
            domain_data=sample_context.domain_data,
            conversation_history=[{"role": "user", "content": "Create a lesson plan"}],
        )
        messages = await agent.build_messages(ctx, uuid4())
        user_msg = messages[-1]["content"]
        assert "Conversation History" in user_msg


class TestLessonPlanningAgentParseResponse:
    @pytest.mark.asyncio
    async def test_parse_valid_json_response(self, agent, sample_context):
        valid_response = json.dumps({
            "title": "Test Lesson",
            "learning_objectives": ["Obj1"],
            "procedure": {"introductory_activity": "intro", "main_activity": "main", "closing_activity": "closing"},
        })
        result = await agent.parse_response(valid_response, sample_context)
        assert result["title"] == "Test Lesson"
        assert len(result["learning_objectives"]) == 1

    @pytest.mark.asyncio
    async def test_parse_json_in_code_block(self, agent, sample_context):
        code_block = '```json\n{"title": "Lesson", "learning_objectives": ["A"], "procedure": {"introductory_activity": "", "main_activity": "", "closing_activity": ""}}\n```'
        result = await agent.parse_response(code_block, sample_context)
        assert result["title"] == "Lesson"
        assert "parse_error" not in result or not result["parse_error"]

    @pytest.mark.asyncio
    async def test_parse_invalid_json_fallback(self, agent, sample_context):
        result = await agent.parse_response("Not json at all", sample_context)
        assert "raw_content" in result
        assert result["grade_level"] == "Grade 3"

    @pytest.mark.asyncio
    async def test_parse_empty_response(self, agent, sample_context):
        result = await agent.parse_response("", sample_context)
        assert "parse_error" not in result or not result["parse_error"] or result.get("title", "") != ""

    @pytest.mark.asyncio
    async def test_output_schema_has_required_fields(self, agent):
        schema = agent.get_output_schema()
        assert "properties" in schema
        assert "title" in schema["properties"]
        assert "learning_objectives" in schema["properties"]
        assert "procedure" in schema["properties"]
        assert "required" in schema
        assert "title" in schema["required"]
        assert "learning_objectives" in schema["required"]


class TestLessonPlanningAgentFullRun:
    @pytest.mark.asyncio
    async def test_agent_kind_assigned(self, agent):
        assert agent.kind.value == "lesson_planning"

    @pytest.mark.asyncio
    async def test_agent_default_model_configured(self, agent):
        assert agent.default_model.provider == "openai"
        assert agent.default_model.model_name == "gpt-4o"

    @pytest.mark.asyncio
    async def test_agent_risk_level(self, agent):
        assert agent.risk_level == "medium"

    @pytest.mark.asyncio
    async def test_agent_required_tools(self, agent):
        assert "curriculum_search" in agent.required_tools
        assert "melc_lookup" in agent.required_tools

    @pytest.mark.asyncio
    async def test_agent_get_rag_query(self, agent, sample_context):
        query = await agent.get_rag_query(sample_context)
        assert query is not None
        assert "Mathematics" in query

    @pytest.mark.asyncio
    async def test_run_with_fake_llm(self, agent, llm, sample_context):
        # Verify the agent and LLM can communicate
        llm.program_response("lesson_planning", json.dumps({
            "title": "Test Generated Lesson",
            "learning_objectives": ["Objective 1"],
            "procedure": {"introductory_activity": "A", "main_activity": "B", "closing_activity": "C"},
        }))
        messages = await agent.build_messages(sample_context, uuid4())
        assert llm.call_count == 0
        response = await llm.chat(messages, agent.default_model)
        assert llm.call_count == 1
        result = await agent.parse_response(response, sample_context)
        # Verify result has expected structure
        assert "title" in result
        assert "learning_objectives" in result
        assert "procedure" in result
