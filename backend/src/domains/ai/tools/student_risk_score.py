"""Student Risk Score Tool — writes a risk assessment score."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from .base_tool import AITool


class StudentRiskScoreTool(AITool):
    name = "student_risk_score"
    description = "Write a risk assessment score for a student"
    requires_tenant = True
    has_side_effects = True

    async def execute(self, arguments: Dict[str, Any], *, tenant_id: UUID, user_id: UUID, run_id: UUID) -> Dict[str, Any]:
        student_id = arguments.get("student_id")
        risk_score = arguments.get("risk_score", 1)
        return {"recorded": True, "student_id": student_id, "risk_score": risk_score}

    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {
            "student_id": {"type": "string"}, "risk_score": {"type": "integer", "minimum": 1, "maximum": 5},
            "risk_level": {"type": "string"}, "risk_factors": {"type": "array", "items": {"type": "string"}},
        }, "required": ["student_id", "risk_score"]}