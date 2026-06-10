"""Curriculum Search Tool — search MELC database by subject, grade, quarter."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from .base_tool import AITool


class CurriculumSearchTool(AITool):
    """Search the MELC (Most Essential Learning Competencies) database."""

    name = "curriculum_search"
    description = "Search the MELC database by subject, grade level, and quarter to find relevant learning competencies"
    requires_tenant = True
    has_side_effects = False

    async def execute(
        self,
        arguments: Dict[str, Any],
        *,
        tenant_id: UUID,
        user_id: UUID,
        run_id: UUID,
    ) -> Dict[str, Any]:
        subject = arguments.get("subject", "")
        grade_level = arguments.get("grade_level", "")
        quarter = arguments.get("quarter")
        topic = arguments.get("topic", "")

        # In production, this queries the curriculum database
        # For MVP, return structured search parameters
        results = []
        filters = []
        if subject:
            filters.append(f"subject={subject}")
        if grade_level:
            filters.append(f"grade={grade_level}")
        if quarter:
            filters.append(f"quarter={quarter}")
        if topic:
            filters.append(f"topic={topic}")

        return {
            "query": {
                "subject": subject,
                "grade_level": grade_level,
                "quarter": quarter,
                "topic": topic,
            },
            "filters_applied": filters,
            "result_count": 0,
            "results": results,
            "message": f"Curriculum search: {', '.join(filters) if filters else 'no filters'}",
        }

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Subject area (e.g., Mathematics, English, Science, Filipino, AP, ESP, MAPEH, TLE)",
                },
                "grade_level": {
                    "type": "string",
                    "description": "Grade level (e.g., Grade 3, Grade 7, SHS)",
                },
                "quarter": {
                    "type": "integer",
                    "description": "Quarter number (1-4)",
                    "minimum": 1,
                    "maximum": 4,
                },
                "topic": {
                    "type": "string",
                    "description": "Topic or keyword to search for",
                },
            },
            "required": [],
        }