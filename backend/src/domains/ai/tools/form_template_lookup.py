"""Form Template Lookup Tool — retrieves DepEd form template structure."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from .base_tool import AITool


class FormTemplateLookupTool(AITool):
    name = "form_template_lookup"
    description = "Retrieve DepEd form template structure by form code"
    requires_tenant = True
    has_side_effects = False

    async def execute(self, arguments: Dict[str, Any], *, tenant_id: UUID, user_id: UUID, run_id: UUID) -> Dict[str, Any]:
        form_code = arguments.get("form_code", "SF9")
        return {"template": {}, "form_code": form_code, "found": False}

    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"form_code": {"type": "string", "description": "DepEd form code (e.g. SF9, SF10)"}}, "required": ["form_code"]}