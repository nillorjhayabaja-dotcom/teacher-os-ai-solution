"""Report Agent — generates summary reports and RPMS compliance documents."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ..value_objects import AgentKind, AIInputContext, ModelConfig
from .base_agent import BaseAgent


class ReportAgent(BaseAgent):
    """Generates summary reports, quarterly accomplishment reports, and RPMS documents."""

    kind = AgentKind.REPORT
    name = "Report Agent"
    description = "Generates summary reports, quarterly accomplishment reports, and RPMS-aligned compliance documents"
    default_model = ModelConfig(provider="openai", model_name="gpt-4o", temperature=0.5, max_tokens=4096)
    required_tools = ["school_config_lookup"]
    optional_tools = ["melc_lookup", "attendance_analyzer"]
    risk_level = "medium"

    async def build_messages(self, context: AIInputContext, prompt_version_id: Any) -> List[Dict[str, str]]:
        domain = context.domain_data
        report_type = domain.get("report_type", "quarterly_accomplishment")
        school_year = domain.get("school_year", "")
        quarter = domain.get("quarter", 0)
        include_stats = domain.get("include_statistics", True)

        system_prompt = (
            "You are a DepEd report generation specialist. You create comprehensive, "
            "well-structured summary reports for Philippine public schools.\n\n"
            "Report types supported:\n"
            "- quarterly_accomplishment: Quarterly accomplishment report\n"
            "- annual_summary: End-of-year summary report\n"
            "- rpms_report: RPMS-aligned performance report\n"
            "- class_summary: Per-class/section summary report\n"
            "- subject_summary: Per-subject summary report\n\n"
            "Follow DepEd reporting standards and include necessary data tables.\n"
            "All outputs must be in valid JSON."
        )
        user_prompt = (
            f"Generate a {report_type.replace('_', ' ').title()} for:\n"
            f"School Year: {school_year}\n"
            f"{f'Quarter: {quarter}' if quarter else ''}\n"
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
            return {"report_type": context.domain_data.get("report_type", ""), "raw_content": raw_response, "parse_error": "Not valid JSON"}
        return {
            "report_type": parsed.get("report_type", context.domain_data.get("report_type", "")),
            "title": parsed.get("title", ""),
            "school_year": parsed.get("school_year", context.domain_data.get("school_year", "")),
            "generated_at": parsed.get("generated_at", ""),
            "executive_summary": parsed.get("executive_summary", ""),
            "sections": parsed.get("sections", []),
            "statistics": parsed.get("statistics", {}),
            "recommendations": parsed.get("recommendations", []),
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "report_type": {"type": "string"},
                "title": {"type": "string"},
                "school_year": {"type": "string"},
                "executive_summary": {"type": "string"},
                "sections": {"type": "array", "items": {"type": "object", "properties": {"heading": {"type": "string"}, "content": {"type": "string"}}}},
                "statistics": {"type": "object"},
                "recommendations": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["report_type", "title", "sections"],
        }

    async def get_rag_query(self, context: AIInputContext) -> str | None:
        return f"DepEd {context.domain_data.get('report_type', 'quarterly')} report template format"