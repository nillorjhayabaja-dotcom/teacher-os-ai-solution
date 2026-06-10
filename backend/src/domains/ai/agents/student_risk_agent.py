"""Student Risk Assessment Agent — analyzes student data to identify at-risk students."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ..value_objects import AgentKind, AIInputContext, ModelConfig
from .base_agent import BaseAgent


class StudentRiskAgent(BaseAgent):
    """Analyzes student data to identify at-risk students and suggest interventions."""

    kind = AgentKind.STUDENT_RISK
    name = "Student Risk Assessment Agent"
    description = (
        "Analyzes student attendance, grades, and behavioral data to identify "
        "at-risk students and suggest targeted interventions"
    )
    default_model = ModelConfig(
        provider="openai",
        model_name="gpt-4o",
        temperature=0.3,
        max_tokens=2048,
    )
    required_tools = ["student_search", "attendance_analyzer", "grade_lookup"]
    optional_tools = ["student_risk_score"]
    risk_level = "low"

    async def build_messages(
        self,
        context: AIInputContext,
        prompt_version_id: Any,
    ) -> List[Dict[str, str]]:
        """Assemble messages for risk assessment."""
        domain = context.domain_data
        students = domain.get("students", [])
        section = domain.get("section", "")
        grading_period = domain.get("grading_period", "current")

        context_str = ""
        if students:
            for s in students[:10]:
                context_str += (
                    f"\nStudent: {s.get('name', 'Unknown')}"
                    f"\n  LRN: {s.get('lrn', 'N/A')}"
                    f"\n  Grade Level: {s.get('grade_level', 'N/A')}"
                    f"\n  Attendance Rate: {s.get('attendance_rate', 'N/A')}%"
                    f"\n  Average Grade: {s.get('avg_grade', 'N/A')}"
                    f"\n  Behavior Notes: {s.get('behavior_notes', 'None')}"
                )

        system_prompt = (
            "You are a student risk assessment analyst for Philippine public schools. "
            "Your role is to identify at-risk students based on academic, attendance, "
            "and behavioral indicators, and provide evidence-based intervention recommendations.\n\n"
            "Risk Factors to Consider:\n"
            "1. Academic Performance: Grades below 75 (failing), declining trend over quarters\n"
            "2. Attendance: Absenteeism rate above 20%, frequent tardiness\n"
            "3. Behavioral: Disciplinary referrals, lack of engagement\n"
            "4. Social Indicators: Limited parental involvement, socioeconomic factors\n\n"
            "Output must be valid JSON following the specified schema."
        )

        user_prompt = (
            f"Analyze the following student data and provide risk assessments.\n"
            f"Section: {section}\n"
            f"Grading Period: {grading_period}\n"
            f"Number of Students: {len(students)}\n"
            f"Student Data:\n{context_str}"
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
        """Parse risk assessment response into structured output."""
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
                "overall_summary": "Risk assessment (raw)",
                "students_analyzed": len(context.domain_data.get("students", [])),
                "at_risk_count": 0,
                "assessments": [],
                "raw_content": raw_response,
                "parse_error": "Response was not valid JSON",
            }

        return {
            "overall_summary": parsed.get("overall_summary", "Risk assessment completed"),
            "generated_at": parsed.get("generated_at", ""),
            "students_analyzed": len(context.domain_data.get("students", [])),
            "at_risk_count": parsed.get("at_risk_count", 0),
            "assessments": parsed.get("assessments", []),
            "recommendations": parsed.get("recommendations", []),
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "overall_summary": {"type": "string"},
                "generated_at": {"type": "string"},
                "students_analyzed": {"type": "integer"},
                "at_risk_count": {"type": "integer"},
                "assessments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "student_name": {"type": "string"},
                            "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                            "risk_score": {"type": "number"},
                            "attendance_impact": {"type": "string"},
                            "academic_impact": {"type": "string"},
                            "behavioral_impact": {"type": "string"},
                            "recommended_intervention": {"type": "string"},
                        },
                    },
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["overall_summary", "assessments"],
        }

    async def get_rag_query(self, context: AIInputContext) -> str | None:
        return "student risk assessment intervention strategies DepEd"