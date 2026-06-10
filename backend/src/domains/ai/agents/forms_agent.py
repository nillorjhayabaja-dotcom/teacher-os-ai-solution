"""Forms Agent — generates DepEd school forms from data."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ..value_objects import AgentKind, AIInputContext, ModelConfig
from .base_agent import BaseAgent


class FormsAgent(BaseAgent):
    """Generates DepEd school forms (SF1-SF10) from provided data."""

    kind = AgentKind.FORMS
    name = "Forms Agent"
    description = "Generates DepEd school forms (SF1-SF10) from provided student and academic data"
    default_model = ModelConfig(provider="openai", model_name="gpt-4o", temperature=0.3, max_tokens=4096)
    required_tools = ["form_template_lookup", "form_validator"]
    optional_tools = ["school_config_lookup"]
    risk_level = "medium"

    async def build_messages(self, context: AIInputContext, prompt_version_id: Any) -> List[Dict[str, str]]:
        domain = context.domain_data
        form_code = domain.get("form_code", "SF9")
        school_year = domain.get("school_year", "")
        quarter = domain.get("quarter", 1)

        system_prompt = (
            "You are a DepEd school forms specialist. You generate accurate DepEd school forms "
            "based on the Department of Education's prescribed formats and guidelines.\n\n"
            "Supported Forms:\n"
            "- SF1 (School Register)\n- SF2 (Daily Attendance Report)\n"
            "- SF3 (Summary of Grades)\n- SF4 (SHS Report Card)\n"
            "- SF5 (Report on Promotion)\n- SF5-A (Learner's Movement)\n"
            "- SF6 (Cumulative Record)\n- SF7 (School Form 7)\n"
            "- SF8 (Learner's Basic Profile)\n- SF9 (Progress Report Card)\n"
            "- SF10 (Learner's Permanent Record)\n\n"
            "Follow DepEd Order 4, s. 2014 and DO 31, s. 2020 for format standards.\n"
            "Output must be valid JSON with the form structure matching the official template."
        )
        user_prompt = (
            f"Generate a {form_code} for:\nSchool Year: {school_year}\nQuarter: {quarter}\n"
            f"Data: {json.dumps(domain, indent=2)[:2000]}"
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
            return {"form_code": context.domain_data.get("form_code", ""), "raw_content": raw_response, "parse_error": "Not valid JSON"}
        return {
            "form_code": parsed.get("form_code", context.domain_data.get("form_code", "")),
            "school_year": parsed.get("school_year", context.domain_data.get("school_year", "")),
            "quarter": parsed.get("quarter", context.domain_data.get("quarter", 1)),
            "sections": parsed.get("sections", {}),
            "data_entries": parsed.get("data_entries", []),
            "summary": parsed.get("summary", ""),
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "form_code": {"type": "string"},
                "school_year": {"type": "string"},
                "quarter": {"type": "integer"},
                "sections": {"type": "object"},
                "data_entries": {"type": "array"},
                "summary": {"type": "string"},
            },
            "required": ["form_code", "sections"],
        }

    async def get_rag_query(self, context: AIInputContext) -> str | None:
        return f"DepEd {context.domain_data.get('form_code', 'SF9')} school form template format"