"""Component tests for StudentRiskAgent."""

import pytest
import json
from uuid import uuid4

from backend.src.domains.ai.agents.student_risk_agent import StudentRiskAgent
from backend.src.domains.ai.value_objects import AIInputContext


@pytest.fixture
def agent():
    return StudentRiskAgent()


@pytest.fixture
def sample_context():
    return AIInputContext(
        tenant_id=uuid4(),
        agent_kind="student_risk",
        user_id=uuid4(),
        domain_data={
            "section": "Grade 3 - Section A",
            "grading_period": "Q1",
            "students": [
                {"name": "Juan Dela Cruz", "attendance_rate": 85, "avg_grade": 78, "lrn": "12-34567-89-01234"},
                {"name": "Maria Santos", "attendance_rate": 45, "avg_grade": 72, "lrn": "12-34567-89-01235"},
            ],
        },
    )


class TestStudentRiskAgent:
    @pytest.mark.asyncio
    async def test_agent_kind(self, agent):
        assert agent.kind.value == "student_risk"
        assert agent.risk_level == "low"

    @pytest.mark.asyncio
    async def test_build_messages(self, agent, sample_context):
        messages = await agent.build_messages(sample_context, uuid4())
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "attendance" in messages[0]["content"].lower()

    @pytest.mark.asyncio
    async def test_build_messages_includes_student_data(self, agent, sample_context):
        messages = await agent.build_messages(sample_context, uuid4())
        assert "Juan Dela Cruz" in messages[1]["content"]
        assert "Maria Santos" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_parse_valid_response(self, agent, sample_context):
        response = json.dumps({
            "overall_summary": "2 students at risk",
            "at_risk_count": 1,
            "assessments": [
                {"student_name": "Maria Santos", "risk_level": "high", "risk_score": 85, "recommended_intervention": "Tutoring"},
            ],
            "recommendations": ["Provide math remediation"],
        })
        result = await agent.parse_response(response, sample_context)
        assert result["at_risk_count"] == 1
        assert len(result["assessments"]) == 1

    @pytest.mark.asyncio
    async def test_parse_invalid_response_fallback(self, agent, sample_context):
        result = await agent.parse_response("Not json", sample_context)
        assert "raw_content" in result

    @pytest.mark.asyncio
    async def test_output_schema(self, agent):
        schema = agent.get_output_schema()
        assert "assessments" in schema["properties"]
        assert "overall_summary" in schema["required"]

    @pytest.mark.asyncio
    async def test_rag_query(self, agent, sample_context):
        query = await agent.get_rag_query(sample_context)
        assert query is not None
        assert "risk assessment" in query.lower()

    @pytest.mark.asyncio
    async def test_required_tools(self, agent):
        assert "student_search" in agent.required_tools
        assert "attendance_analyzer" in agent.required_tools
        assert "grade_lookup" in agent.required_tools