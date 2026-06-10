"""Communication Agent — drafts parent-teacher communication messages."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ..value_objects import AgentKind, AIInputContext, ModelConfig
from .base_agent import BaseAgent


class CommunicationAgent(BaseAgent):
    """Drafts parent-teacher communication messages with appropriate tone and content."""

    kind = AgentKind.COMMUNICATION
    name = "Communication Agent"
    description = "Drafts parent-teacher communication messages including progress updates, concern letters, and invitations"
    default_model = ModelConfig(provider="openai", model_name="gpt-4o", temperature=0.7, max_tokens=2048)
    required_tools = ["student_search"]
    optional_tools = ["notification_sender"]
    risk_level = "high"

    async def build_messages(self, context: AIInputContext, prompt_version_id: Any) -> List[Dict[str, str]]:
        domain = context.domain_data
        comm_type = domain.get("comm_type", "academic_progress")
        recipient = domain.get("recipient", "parent")
        student_name = domain.get("student_name", "")
        parent_name = domain.get("parent_name", "")
        subject = domain.get("subject", "")
        teacher_name = domain.get("teacher_name", "Teacher")
        language = domain.get("language", "English")
        tone = domain.get("tone", "formal")

        system_prompt = (
            "You are a professional school communication assistant. You draft clear, "
            "respectful, and culturally appropriate messages for parent-teacher communication "
            "in Philippine public schools.\n\n"
            "Communication types:\n"
            "- academic_progress: Update on student's academic performance\n"
            "- behavior_concern: Notify about behavioral issues\n"
            "- attendance_concern: Notify about absenteeism\n"
            "- event_invitation: Invite to school events\n"
            "- general_update: General progress update\n"
            "- meeting_request: Request for parent-teacher meeting\n\n"
            "Guidelines:\n"
            "1. Be respectful and culturally sensitive to Filipino values\n"
            "2. Use encouraging and constructive language\n"
            "3. Include specific, actionable information\n"
            "4. Offer solutions and collaborative approaches\n"
            f"5. Write in {language} with a {tone} tone\n"
            "6. Include contact information for follow-up\n\n"
            "Output must be valid JSON."
        )
        user_prompt = (
            f"Draft a {comm_type.replace('_', ' ')} message:\n"
            f"To: {recipient} ({parent_name})\n"
            f"Regarding Student: {student_name}\n"
            f"Subject: {subject}\n"
            f"From: {teacher_name}\n"
            f"Language: {language}\n"
            f"Tone: {tone}\n"
            f"Context: {domain.get('context', '')}"
        )
        return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    async def parse_response(self, raw_response: str, context: AIInputContext) -> Dict[str, Any]:
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"): cleaned = cleaned[7:]
        if cleaned.startswith("```"): cleaned = cleaned[3:]
        if cleaned.endswith("```"): cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return {"comm_type": context.domain_data.get("comm_type", ""), "raw_content": raw_response, "parse_error": "Not valid JSON"}
        return {
            "comm_type": parsed.get("comm_type", context.domain_data.get("comm_type", "")),
            "subject_line": parsed.get("subject_line", ""),
            "greeting": parsed.get("greeting", ""),
            "body": parsed.get("body", ""),
            "closing": parsed.get("closing", ""),
            "tone_notes": parsed.get("tone_notes", ""),
            "recommended_channel": parsed.get("recommended_channel", "email"),
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "comm_type": {"type": "string"},
                "subject_line": {"type": "string"},
                "greeting": {"type": "string"},
                "body": {"type": "string"},
                "closing": {"type": "string"},
                "tone_notes": {"type": "string"},
                "recommended_channel": {"type": "string", "enum": ["email", "sms", "viber", "printed"]},
            },
            "required": ["body", "comm_type"],
        }

    async def get_rag_query(self, context: AIInputContext) -> str | None:
        return "DepEd parent-teacher communication guidelines best practices"