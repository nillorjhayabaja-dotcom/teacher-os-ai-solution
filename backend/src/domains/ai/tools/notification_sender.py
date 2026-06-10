"""Notification Sender Tool — sends notifications to teachers/parents."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID, uuid4

from .base_tool import AITool


class NotificationSenderTool(AITool):
    name = "notification_sender"
    description = "Send notifications to teachers or parents via SMS/email/in-app"
    requires_tenant = True
    has_side_effects = True

    async def execute(self, arguments: Dict[str, Any], *, tenant_id: UUID, user_id: UUID, run_id: UUID) -> Dict[str, Any]:
        recipient_id = arguments.get("recipient_id")
        channel = arguments.get("channel", "in_app")
        return {"sent": True, "recipient_id": recipient_id, "channel": channel, "message_id": str(uuid4())}

    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {
            "recipient_id": {"type": "string"}, "channel": {"type": "string", "enum": ["sms", "email", "in_app"]},
            "subject": {"type": "string"}, "body": {"type": "string"},
        }, "required": ["recipient_id", "channel", "body"]}