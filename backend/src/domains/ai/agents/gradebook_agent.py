"""Gradebook Agent — analyzes grades and suggests grade computation improvements."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ..value_objects import AgentKind, AIInputContext, ModelConfig
from .base_agent import BaseAgent


class GradebookAgent(BaseAgent):
    """Analyzes grade data, suggests improvements, and generates grade computations."""

    kind = AgentKind.GRADEBOOK
    name = "Gradebook Agent"
    description = (
        "Analyzes student grade data, suggests interventions for low-performing "
        "students, and assists with DepEd transmutation and grade computation"
    )
    default_model = ModelConfig(
        provider="openai",
        model_name="gpt-4o",
        temperature=0.4,
        max_tokens=3072,
    )
    required_tools = ["grade_lookup", "transmutation_lookup"]
    optional_tools = ["student_search"]
    risk_level = "medium"

    async def build_messages(self, context: AIInputContext, prompt_version_id: Any) -> List[Dict[str, str]]:
        domain = context.domain_data
        students = domain.get("students", [])
        subject = domain.get("subject", "")
        grading_period = domain.get("grading_period", "")
        include_transmutation = domain.get("include_transmutation", True)

        grade_data = ""
        for s in students[:20]:
            grade_data += f"\n{s.get('name', 'Unknown')}: WW={s.get('written_works')}, PT={s.get('performance_tasks')}, QA={s.get('quarterly_assessment')}"

        system_prompt = (
            "You are a DepEd grade computation specialist. You assist teachers with:\n"
            "1. Computing initial and transmuted grades following DepEd Order 8, s. 2015\n"
            "2. Identifying students at risk of failing (below 75)\n"
            "3. Suggesting interventions for low-performing students\n"
            "4. Generating summary reports per subject/section\n\n"
            "Follow the standard DepEd grade computation formula:\n"
            "- Written Works (WW): 30% (for languages) or 20% (for MAPEH/ESP)\n"
            "- Performance Tasks (PT): 50% (for languages) or 60% (for MAPEH/ESP)\n"
            "- Quarterly Assessment (QA): 20%\n\n"
            "Output must be valid JSON."
        )

        user_prompt = (
            f"Analyze the following grade data:\n"
            f"Subject: {subject}\n"
            f"Grading Period: {grading_period}\n"
            f"Number of Students: {len(students)}\n"
            f"Grade Data:{grade_data}\n"
            f"{'Include transmuted grades.' if include_transmutation else ''}"
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
            return {"summary": "Grade computation (raw)", "students": [], "raw_content": raw_response, "parse_error": "Not valid JSON"}

        return {
            "subject": parsed.get("subject", context.domain_data.get("subject", "")),
            "grading_period": parsed.get("grading_period", ""),
            "summary": parsed.get("summary", ""),
            "students": parsed.get("students", []),
            "recommendations": parsed.get("recommendations", []),
            "class_statistics": parsed.get("class_statistics", {}),
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "grading_period": {"type": "string"},
                "summary": {"type": "string"},
                "students": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "initial_grade": {"type": "number"},
                            "transmuted_grade": {"type": "number"},
                            "status": {"type": "string"},
                            "intervention": {"type": "string"},
                        },
                    },
                },
                "recommendations": {"type": "array", "items": {"type": "string"}},
                "class_statistics": {
                    "type": "object",
                    "properties": {
                        "total_students": {"type": "integer"},
                        "passing_count": {"type": "integer"},
                        "failing_count": {"type": "integer"},
                        "average_grade": {"type": "number"},
                        "highest_grade": {"type": "number"},
                        "lowest_grade": {"type": "number"},
                    },
                },
            },
            "required": ["summary", "students"],
        }

    async def get_rag_query(self, context: AIInputContext) -> str | None:
        return "DepEd grade computation transmutation table s.2015"