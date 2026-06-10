"""Rubric Generator Tool — generates rubric criteria from learning objectives."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from .base_tool import AITool


class RubricGeneratorTool(AITool):
    name = "rubric_generator"
    description = "Generate rubric criteria from learning objectives"
    requires_tenant = True
    has_side_effects = False

    async def execute(self, arguments: Dict[str, Any], *, tenant_id: UUID, user_id: UUID, run_id: UUID) -> Dict[str, Any]:
        objectives = arguments.get("objectives", [])
        rubric_type = arguments.get("type", "analytic")
        return {"rubric": {"criteria": [], "levels": [], "type": rubric_type}, "objectives": objectives}

    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {
            "objectives": {"type": "array", "items": {"type": "string"}, "description": "Learning objectives"},
            "type": {"type": "string", "enum": ["analytic", "holistic"], "description": "Rubric type"},
        }, "required": ["objectives"]}