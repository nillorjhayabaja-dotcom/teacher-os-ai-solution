"""School Config Lookup Tool — gets school configuration and settings."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from .base_tool import AITool


class SchoolConfigLookupTool(AITool):
    name = "school_config_lookup"
    description = "Get school configuration, grading policy, and settings"
    requires_tenant = True
    has_side_effects = False

    async def execute(self, arguments: Dict[str, Any], *, tenant_id: UUID, user_id: UUID, run_id: UUID) -> Dict[str, Any]:
        config_key = arguments.get("key", "all")
        return {"config": {}, "key": config_key, "tenant_id": str(tenant_id)}

    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"key": {"type": "string", "description": "Config key to retrieve (or 'all')"}}}