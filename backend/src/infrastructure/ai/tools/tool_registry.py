"""Tool Registry — central registry for all AI tools with auto-registration."""

from __future__ import annotations

from typing import Dict, List, Optional, Type

from backend.src.domains.ai.tools.base_tool import AITool


class ToolRegistry:
    """Central registry for all AI tools.

    Agents reference tools by name. The registry resolves tool instances
    and provides schemas for LLM function calling. Tools are auto-registered
    with default implementations, and can be overridden for testing.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, AITool] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Auto-register all built-in tools."""
        from backend.src.domains.ai.tools.curriculum_search import CurriculumSearchTool
        from backend.src.domains.ai.tools.melc_lookup import MelcLookupTool
        from backend.src.domains.ai.tools.student_search import StudentSearchTool
        from backend.src.domains.ai.tools.attendance_analyzer import AttendanceAnalyzerTool
        from backend.src.domains.ai.tools.grade_lookup import GradeLookupTool
        from backend.src.domains.ai.tools.rubric_generator import RubricGeneratorTool
        from backend.src.domains.ai.tools.form_template_lookup import FormTemplateLookupTool
        from backend.src.domains.ai.tools.transmutation_lookup import TransmutationLookupTool
        from backend.src.domains.ai.tools.notification_sender import NotificationSenderTool
        from backend.src.domains.ai.tools.student_risk_score import StudentRiskScoreTool
        from backend.src.domains.ai.tools.form_validator import FormValidatorTool
        from backend.src.domains.ai.tools.school_config_lookup import SchoolConfigLookupTool

        for tool_cls in [
            CurriculumSearchTool,
            MelcLookupTool,
            StudentSearchTool,
            AttendanceAnalyzerTool,
            GradeLookupTool,
            RubricGeneratorTool,
            FormTemplateLookupTool,
            TransmutationLookupTool,
            NotificationSenderTool,
            StudentRiskScoreTool,
            FormValidatorTool,
            SchoolConfigLookupTool,
        ]:
            tool = tool_cls()
            self._tools[tool.name] = tool

    def register(self, tool: AITool) -> None:
        """Register a custom or overridden tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[AITool]:
        """Get a tool by name. Returns None if not found."""
        return self._tools.get(name)

    def get_or_raise(self, name: str) -> AITool:
        """Get a tool by name. Raises KeyError if not found."""
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool not found: {name}")
        return tool

    def get_schemas_for_agent(self, tool_names: List[str]) -> List[Dict]:
        """Return OpenAI tool schemas for the given tool names."""
        schemas = []
        for name in tool_names:
            tool = self._tools.get(name)
            if tool:
                schemas.append(tool.to_openai_tool())
        return schemas

    def list_all(self) -> List[AITool]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_names(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())