"""MELC Lookup Tool — get specific MELC details by code."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from .base_tool import AITool


class MelcLookupTool(AITool):
    """Look up specific MELC (Most Essential Learning Competency) details by code."""

    name = "melc_lookup"
    description = "Look up specific MELC details by competency code (e.g., M3NS-Ia-1, EN4G-Ia-1)"
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
        melc_code = arguments.get("melc_code", "")
        subject = arguments.get("subject", "")

        # In production, this queries the MELC database
        return {
            "query": {"melc_code": melc_code, "subject": subject},
            "found": False,
            "melc": None,
            "message": f"MELC lookup for {melc_code}: not found in local cache" if melc_code else "No MELC code provided",
        }

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "melc_code": {
                    "type": "string",
                    "description": "MELC competency code (e.g., M3NS-Ia-1, EN4G-Ia-1, S5FE-IIIa-1)",
                },
                "subject": {
                    "type": "string",
                    "description": "Subject area to narrow the search",
                },
            },
            "required": ["melc_code"],
        }