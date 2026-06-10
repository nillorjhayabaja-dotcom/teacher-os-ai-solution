"""Transmutation Lookup Tool — looks up DepEd transmutation table values."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from .base_tool import AITool

# DepEd transmutation table (simplified)
TRANSMUTATION_TABLE = {
    i: max(60, min(100, 60 + (i * 40 // 100))) for i in range(0, 101)
}


class TransmutationLookupTool(AITool):
    name = "transmutation_lookup"
    description = "Look up DepEd transmutation table values"
    requires_tenant = True
    has_side_effects = False

    async def execute(self, arguments: Dict[str, Any], *, tenant_id: UUID, user_id: UUID, run_id: UUID) -> Dict[str, Any]:
        initial_grade = arguments.get("initial_grade", 0)
        transmuted = TRANSMUTATION_TABLE.get(int(initial_grade), initial_grade)
        return {"initial_grade": initial_grade, "transmuted_grade": transmuted}

    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"initial_grade": {"type": "number", "description": "Raw percentage score (initial grade)"}}, "required": ["initial_grade"]}
