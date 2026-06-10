from __future__ import annotations

from uuid import uuid4

import pytest

from backend.src.domains.ai.tools import (
    AttendanceAnalyzerTool,
    CurriculumSearchTool,
    FormTemplateLookupTool,
    FormValidatorTool,
    GradeLookupTool,
    MELCLookupTool,
    NotificationSenderTool,
    RubricGeneratorTool,
    SchoolConfigLookupTool,
    StudentRiskScoreTool,
    StudentSearchTool,
    TransmutationLookupTool,
)
from backend.src.infrastructure.ai.tools.tool_registry import ToolRegistry


@pytest.mark.tools
@pytest.mark.unit
def test_tool_registry_registers_documented_tooling_surface():
    registry = ToolRegistry()
    names = set(registry.list_names())
    assert {
        "curriculum_search",
        "melc_lookup",
        "student_search",
        "attendance_analyzer",
        "grade_lookup",
        "rubric_generator",
        "form_template_lookup",
        "transmutation_lookup",
        "notification_sender",
        "student_risk_score",
        "form_validator",
        "school_config_lookup",
    }.issubset(names)
    assert registry.get("missing") is None


@pytest.mark.tools
@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_cls,args,expected_key",
    [
        (CurriculumSearchTool, {"query": "science"}, "results"),
        (MELCLookupTool, {"subject": "Science", "grade_level": "6", "melc_code": "M3NS-Ia-1"}, "found"),
        (StudentSearchTool, {"name": "Ana"}, "results"),
        (AttendanceAnalyzerTool, {"student_id": "s1"}, "statistics"),
        (GradeLookupTool, {"student_id": "s1"}, "grades"),
        (RubricGeneratorTool, {"task": "essay"}, "rubric"),
        (FormTemplateLookupTool, {"form_type": "SF2"}, "template"),
        (TransmutationLookupTool, {"initial_grade": 90}, "transmuted_grade"),
        (NotificationSenderTool, {"recipient_id": "p1", "channel": "in_app", "body": "Hello"}, "sent"),
        (StudentRiskScoreTool, {"student_id": "s1", "risk_score": 4}, "recorded"),
        (FormValidatorTool, {"form_type": "SF2", "data": {}}, "valid"),
        (SchoolConfigLookupTool, {"key": "grading"}, "config"),
    ],
)
async def test_each_tool_executes_with_tenant_scope(tool_cls, args, expected_key, tenant_id, user_id):
    tool = tool_cls()
    result = await tool.execute(args, tenant_id=tenant_id, user_id=user_id, run_id=uuid4())

    assert expected_key in result
    assert tool.get_schema()["type"] == "object"
    assert tool.requires_tenant is True


@pytest.mark.tools
@pytest.mark.security
@pytest.mark.xfail_architecture_gap(reason="ToolRegistry currently stores tools but does not enforce permissions/audit execution centrally.")
@pytest.mark.asyncio
async def test_tool_registry_enforces_permission_and_audit_logging(tenant_id, user_id):
    registry = ToolRegistry()
    result = await registry.execute(
        "student_risk_score",
        {"student_id": "s1", "risk_score": 5},
        tenant_id=tenant_id,
        user_id=user_id,
        run_id=uuid4(),
        permissions=set(),
    )
    assert result["error"] == "permission_denied"
    assert registry.audit_log[-1]["tool_name"] == "student_risk_score"


@pytest.mark.tools
@pytest.mark.security
@pytest.mark.xfail_architecture_gap(reason="Document/reporting/search tool categories are not modeled as first-class permission groups yet.")
def test_tool_registry_groups_tools_by_document_validation_reporting_search_categories():
    registry = ToolRegistry()
    assert registry.by_category("document")
    assert registry.by_category("validation")
    assert registry.by_category("reporting")