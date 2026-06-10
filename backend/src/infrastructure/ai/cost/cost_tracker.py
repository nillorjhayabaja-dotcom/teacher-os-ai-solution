"""Cost Tracker — tracks per-tenant AI spending."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID


class CostTracker:
    """Tracks AI costs per tenant, per day, per agent, per model."""

    def __init__(self, session=None) -> None:
        self._session = session

    async def record_cost(
        self,
        *,
        tenant_id: UUID,
        agent_kind: str,
        model_used: str,
        cost_cents: float,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        run_id: UUID,
    ) -> None:
        """Record cost for a single AI run."""
        pass  # In production, INSERT into ai.agent_runs

    async def get_daily_summary(
        self, tenant_id: UUID, target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        if target_date is None:
            target_date = date.today()
        return {
            "tenant_id": str(tenant_id),
            "date": target_date.isoformat(),
            "total_cost_cents": 0.0,
            "total_runs": 0,
            "total_tokens": 0,
            "by_agent": {},
            "by_model": {},
        }

    async def get_monthly_summary(self, tenant_id: UUID) -> Dict[str, Any]:
        return {
            "tenant_id": str(tenant_id),
            "total_cost_cents": 0.0,
            "total_runs": 0,
            "total_tokens": 0,
            "budget_remaining_cents": 5000.0,
        }

    async def get_cost_by_agent(self, tenant_id: UUID, days: int = 30) -> List[Dict]:
        return []

    async def get_cost_by_model(self, tenant_id: UUID, days: int = 30) -> List[Dict]:
        return []

    async def get_daily_trend(self, tenant_id: UUID, days: int = 30) -> List[Dict]:
        return []