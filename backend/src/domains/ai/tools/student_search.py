"""Student Search Tool — search students by name, LRN, grade level."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from .base_tool import AITool


class StudentSearchTool(AITool):
    """Search students by name, LRN, grade level, or section."""

    name = "student_search"
    description = "Search for students by name, LRN, grade level, or section"
    requires_tenant = True
    has_side_effects = False

    async def execute(self, arguments: Dict[str, Any], *, tenant_id: UUID, user_id: UUID, run_id: UUID) -> Dict[str, Any]:
        return {
            "query": {"name": arguments.get("name"), "lrn": arguments.get("lrn"), "grade_level": arguments.get("grade_level"), "section": arguments.get("section")},
            "result_count": 0, "results": [], "message": "Student search: no local data available",
        }

    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {
            "name": {"type": "string", "description": "Student name to search for"},
            "lrn": {"type": "string", "description": "Learner Reference Number"},
            "grade_level": {"type": "string", "description": "Grade level filter"},
            "section": {"type": "string", "description": "Section/class filter"},
        }, "anyOf": [{"required": ["name"]}, {"required": ["lrn"]}]}