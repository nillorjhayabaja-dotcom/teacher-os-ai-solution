"""Lesson Planning Agent — generates DepEd-aligned lesson plans."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ..value_objects import AgentKind, AIInputContext, ModelConfig
from .base_agent import BaseAgent


class LessonPlanningAgent(BaseAgent):
    """Generates DepEd-aligned lesson plans with objectives, procedure, and activities."""

    kind = AgentKind.LESSON_PLANNING
    name = "Lesson Planning Agent"
    description = (
        "Generates DepEd-aligned lesson plans with learning objectives, "
        "instructional procedure, materials, and assessment activities"
    )
    default_model = ModelConfig(
        provider="openai",
        model_name="gpt-4o",
        temperature=0.7,
        max_tokens=4096,
    )
    required_tools = ["curriculum_search", "melc_lookup"]
    optional_tools = ["student_search", "rubric_generator"]
    risk_level = "medium"

    async def build_messages(
        self,
        context: AIInputContext,
        prompt_version_id: Any,
    ) -> List[Dict[str, str]]:
        """Assemble the message array for lesson plan generation."""
        domain = context.domain_data
        grade = domain.get("grade_level", "Unknown Grade")
        subject = domain.get("subject", "Unknown Subject")
        topic = domain.get("topic", "")
        duration = domain.get("duration_minutes", 60)

        # Build RAG context string if available
        rag_section = ""
        if context.rag_context:
            rag_section = "\n\nReference Materials:\n"
            for i, chunk in enumerate(context.rag_context[:5], 1):
                rag_section += f"\n[{i}] {chunk.get('content', '')[:500]}"

        # Build conversation history if available
        history_section = ""
        if context.conversation_history:
            history_section = "\n\nConversation History:\n"
            for msg in context.conversation_history[-5:]:
                role = msg.get("role", "unknown")
                content = str(msg.get("content", ""))[:200]
                history_section += f"\n{role}: {content}"

        system_prompt = (
            "You are a DepEd-aligned lesson planning assistant for Philippine public schools. "
            "You must generate lesson plans that follow the Department of Education (DepEd) "
            "standards and the Most Essential Learning Competencies (MELCs).\n\n"
            "Your output must be valid JSON following the specified schema exactly.\n\n"
            "Guidelines:\n"
            "1. All learning objectives must be specific, measurable, and aligned to MELCs\n"
            "2. Include differentiated instruction for diverse learners\n"
            "3. Use the 4A's model (Activity, Analysis, Abstraction, Application)\n"
            "4. Include formative assessment strategies\n"
            "5. Specify appropriate instructional materials\n"
            "6. Ensure cultural relevance and contextualization\n"
            "7. Follow the standard DLL/DLP format"
        )

        user_prompt = (
            f"Create a detailed lesson plan for:\n"
            f"Grade Level: {grade}\n"
            f"Subject: {subject}\n"
            f"{f'Topic: {topic}' if topic else ''}\n"
            f"Duration: {duration} minutes\n"
            f"{rag_section}"
            f"{history_section}"
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    async def parse_response(
        self,
        raw_response: str,
        context: AIInputContext,
    ) -> Dict[str, Any]:
        """Parse and validate the LLM response into a structured lesson plan."""
        # Attempt to extract JSON from the response
        cleaned = raw_response.strip()
        # Handle code block wrapping
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # If not valid JSON, wrap the raw text as content
            return {
                "title": context.domain_data.get("topic", "Lesson Plan"),
                "grade_level": context.domain_data.get("grade_level", ""),
                "subject": context.domain_data.get("subject", ""),
                "raw_content": raw_response,
                "parse_error": "Response was not valid JSON, stored as raw text",
            }

        # Validate required fields per the output schema
        validated = {
            "title": parsed.get("title", context.domain_data.get("topic", "Untitled Lesson")),
            "grade_level": parsed.get("grade_level", context.domain_data.get("grade_level", "")),
            "subject": parsed.get("subject", context.domain_data.get("subject", "")),
            "learning_objectives": parsed.get("learning_objectives", []),
            "materials": parsed.get("materials", []),
            "procedure": parsed.get("procedure", {
                "introductory_activity": "",
                "main_activity": "",
                "closing_activity": "",
            }),
            "assessment": parsed.get("assessment", ""),
            "remarks": parsed.get("remarks", ""),
        }
        return validated

    def get_output_schema(self) -> Dict[str, Any]:
        """Return the JSON Schema for lesson plan output."""
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Lesson plan title"},
                "grade_level": {"type": "string", "description": "Target grade level"},
                "subject": {"type": "string", "description": "Subject area"},
                "learning_objectives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific, measurable learning objectives",
                },
                "materials": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Required instructional materials",
                },
                "procedure": {
                    "type": "object",
                    "properties": {
                        "introductory_activity": {"type": "string"},
                        "main_activity": {"type": "string"},
                        "closing_activity": {"type": "string"},
                    },
                    "description": "Lesson procedure using 4A's model",
                },
                "assessment": {"type": "string", "description": "Formative assessment strategy"},
                "remarks": {"type": "string", "description": "Additional remarks and notes"},
            },
            "required": ["title", "learning_objectives", "procedure"],
        }

    async def get_rag_query(self, context: AIInputContext) -> str | None:
        """Generate RAG query for relevant MELCs and exemplar lesson plans."""
        domain = context.domain_data
        grade = domain.get("grade_level", "")
        subject = domain.get("subject", "")
        topic = domain.get("topic", "")
        query = f"{grade} {subject} {topic} MELC lesson plan".strip()
        return query if query else None