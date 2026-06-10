"""Assessment Agent — creates quiz items, rubrics, and formative assessments aligned to MELCs."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ..value_objects import AgentKind, AIInputContext, ModelConfig
from .base_agent import BaseAgent


class AssessmentAgent(BaseAgent):
    """Creates quiz items, rubrics, and formative assessments aligned to MELCs."""

    kind = AgentKind.ASSESSMENT
    name = "Assessment Agent"
    description = (
        "Creates quiz items, rubrics, and formative assessments "
        "aligned to Most Essential Learning Competencies (MELCs)"
    )
    default_model = ModelConfig(
        provider="openai",
        model_name="gpt-4o",
        temperature=0.6,
        max_tokens=4096,
    )
    required_tools = ["melc_lookup", "rubric_generator"]
    optional_tools = ["curriculum_search"]
    risk_level = "medium"

    async def build_messages(
        self,
        context: AIInputContext,
        prompt_version_id: Any,
    ) -> List[Dict[str, str]]:
        domain = context.domain_data
        grade = domain.get("grade_level", "Unknown Grade")
        subject = domain.get("subject", "Unknown Subject")
        topic = domain.get("topic", "")
        num_items = domain.get("num_items", 10)
        item_types = domain.get("item_types", ["multiple_choice", "true_false", "short_answer"])
        difficulty = domain.get("difficulty", "mixed")

        system_prompt = (
            "You are a DepEd-aligned assessment item writer for Philippine public schools. "
            "You create valid, reliable, and fair assessment items aligned to MELCs.\n\n"
            "Guidelines:\n"
            "1. All items must align to specific MELC codes and competencies\n"
            "2. Use clear, unambiguous language appropriate for the grade level\n"
            "3. Include a mix of difficulty levels (easy: 30%, average: 50%, difficult: 20%)\n"
            "4. Provide distractors (wrong answers) that are plausible but incorrect\n"
            "5. Include the correct answer and a brief rationale for each item\n"
            "6. Follow DepEd item writing guidelines and avoid cultural bias\n"
            "7. For rubrics: use 4-point scales with clear descriptors\n\n"
            "Output must be valid JSON."
        )

        user_prompt = (
            f"Create assessment items for:\n"
            f"Grade Level: {grade}\n"
            f"Subject: {subject}\n"
            f"Topic: {topic}\n"
            f"Number of Items: {num_items}\n"
            f"Item Types: {', '.join(item_types)}\n"
            f"Difficulty: {difficulty}\n"
            f"{'Include a rubric for the assessment.' if domain.get('include_rubric') else ''}"
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
        cleaned = raw_response.strip()
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
            return {
                "title": f"{context.domain_data.get('subject', '')} Assessment",
                "subject": context.domain_data.get("subject", ""),
                "grade_level": context.domain_data.get("grade_level", ""),
                "items": [],
                "rubric": None,
                "raw_content": raw_response,
                "parse_error": "Response was not valid JSON",
            }

        return {
            "title": parsed.get("title", f"{context.domain_data.get('subject', '')} Assessment"),
            "subject": parsed.get("subject", context.domain_data.get("subject", "")),
            "grade_level": parsed.get("grade_level", context.domain_data.get("grade_level", "")),
            "melc_code": parsed.get("melc_code", ""),
            "total_points": parsed.get("total_points", 0),
            "items": parsed.get("items", []),
            "rubric": parsed.get("rubric"),
            "scoring_guide": parsed.get("scoring_guide", ""),
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "subject": {"type": "string"},
                "grade_level": {"type": "string"},
                "melc_code": {"type": "string"},
                "total_points": {"type": "integer"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_number": {"type": "integer"},
                            "item_type": {"type": "string"},
                            "melc_code": {"type": "string"},
                            "question": {"type": "string"},
                            "options": {"type": "array", "items": {"type": "string"}},
                            "correct_answer": {"type": "string"},
                            "rationale": {"type": "string"},
                            "difficulty": {"type": "string"},
                            "points": {"type": "integer"},
                        },
                    },
                },
                "rubric": {
                    "type": "object",
                    "properties": {
                        "criteria": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "levels": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "score": {"type": "integer"},
                                                "descriptor": {"type": "string"},
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                "scoring_guide": {"type": "string"},
            },
            "required": ["items", "title"],
        }

    async def get_rag_query(self, context: AIInputContext) -> str | None:
        domain = context.domain_data
        return f"{domain.get('grade_level', '')} {domain.get('subject', '')} {domain.get('topic', '')} MELC assessment"