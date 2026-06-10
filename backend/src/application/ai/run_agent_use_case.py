"""Run Agent Use Case — orchestrates the full agent execution flow."""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from backend.src.domains.ai.agents.base_agent import BaseAgent
from backend.src.domains.ai.value_objects import AIInputContext


class RunAgentUseCase:
    """Application use case for executing an AI agent run.

    Orchestrates: security check → budget check → context assembly →
    agent execution → review state assignment.
    """

    def __init__(self, agent_registry, agent_runner, review_gate, budget_manager, prompt_guard):
        self._agent_registry = agent_registry
        self._runner = agent_runner
        self._review_gate = review_gate
        self._budget = budget_manager
        self._guard = prompt_guard

    async def execute(
        self,
        *,
        agent_kind: str,
        tenant_id: UUID,
        user_id: UUID,
        domain_data: Dict[str, Any],
        model_override: Optional[str] = None,
        temperature_override: Optional[float] = None,
        max_tokens_override: Optional[int] = None,
        conversation_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        # Resolve agent
        try:
            agent = self._agent_registry.get(agent_kind)
        except KeyError:
            return {"error": f"Agent not found: {agent_kind}", "status": "failed"}

        # Security: check prompt injection in all string fields of domain_data
        for key, value in domain_data.items():
            if isinstance(value, str):
                detection = self._guard.detect(value)
                if detection:
                    sanitized = self._guard.sanitize(value)
                    if sanitized != value:
                        domain_data[key] = sanitized
                    else:
                        return {
                            "error": "Input rejected",
                            "reason": str(detection),
                            "field": key,
                        }
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        detection = self._guard.detect(sub_value)
                        if detection:
                            sanitized = self._guard.sanitize(sub_value)
                            if sanitized != sub_value:
                                value[sub_key] = sanitized
                            else:
                                return {
                                    "error": "Input rejected",
                                    "reason": str(detection),
                                    "field": f"{key}.{sub_key}",
                                }

        # Budget check
        budget_check = await self._budget.check_budget(tenant_id, estimated_cost_cents=0.0)
        if not budget_check.get("allowed", True):
            return {
                "error": "Budget exceeded",
                "alert_level": budget_check.get("alert_level"),
                "monthly_usage_pct": budget_check.get("monthly_usage_pct"),
                "daily_usage_pct": budget_check.get("daily_usage_pct"),
            }

        # Build input context
        context = AIInputContext(
            tenant_id=tenant_id,
            agent_kind=agent_kind,
            user_id=user_id,
            domain_data=domain_data,
        )

        # Execute agent
        result = await self._runner.run_agent(
            agent,
            context,
            model_override=model_override,
            temperature_override=temperature_override,
            max_tokens_override=max_tokens_override,
        )

        # Determine review state
        if result.get("status") != "failed":
            review_state = self._review_gate.get_initial_review_state(agent_kind)
            result["review_state"] = review_state.value
        else:
            result["review_state"] = "failed"

        return result