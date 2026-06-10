"""AI Event Handlers — handle AI domain events."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AIOutputApprovedHandler:
    """Handle AI output approval — apply to domain context."""

    async def handle(self, event) -> None:
        if getattr(event, "review_state", "") != "approved":
            return

        logger.info(
            "AI output approved: output_id=%s, tenant_id=%s, reviewer_id=%s",
            getattr(event, "output_id", None),
            getattr(event, "tenant_id", None),
            getattr(event, "reviewer_id", None),
        )

        # In production, route to appropriate domain service based on domain_type
        # output = await self.output_repo.get(event.output_id)
        # match output.domain_type:
        #     case "lesson_plan": await self.lesson_service.apply_ai_output(...)
        #     case "assessment": await self.assessment_service.create_from_ai_output(...)
        #     ...


class AIRunCompletedHandler:
    """Handle AI run completion — update metrics and notify."""

    async def handle(self, event) -> None:
        logger.info(
            "AI run completed: run_id=%s, agent_kind=%s, cost_cents=%s, latency_ms=%s",
            getattr(event, "run_id", None),
            getattr(event, "agent_kind", None),
            getattr(event, "cost_cents", 0),
            getattr(event, "latency_ms", 0),
        )

        # In production, update Prometheus metrics
        # from backend.src.observability.ai_metrics import record_agent_run
        # record_agent_run(...)


class AIRunFailedHandler:
    """Handle AI run failure — notify user and log error."""

    async def handle(self, event) -> None:
        logger.error(
            "AI run failed: run_id=%s, error_type=%s, error_message=%s",
            getattr(event, "run_id", None),
            getattr(event, "error_type", None),
            getattr(event, "error_message", None),
        )


class AIBudgetAlertHandler:
    """Handle budget alert — notify admins."""

    async def handle(self, event) -> None:
        alert_level = getattr(event, "alert_level", "warning")
        logger.warning(
            "AI budget alert [%s]: tenant_id=%s, current_spend=%s, limit=%s",
            alert_level,
            getattr(event, "tenant_id", None),
            getattr(event, "current_spend_cents", 0),
            getattr(event, "budget_limit_cents", 0),
        )


class AIToolExecutedHandler:
    """Handle tool execution — update tool metrics."""

    async def handle(self, event) -> None:
        logger.info(
            "AI tool executed: tool=%s, success=%s, latency_ms=%s",
            getattr(event, "tool_name", None),
            getattr(event, "success", False),
            getattr(event, "latency_ms", 0),
        )