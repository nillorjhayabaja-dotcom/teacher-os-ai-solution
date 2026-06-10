"""Budget Manager — manages per-tenant AI budget limits and alerts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from uuid import UUID


@dataclass
class TenantAIBudget:
    tenant_id: UUID
    monthly_limit_cents: float = 5000.00
    daily_limit_cents: float = 500.00
    per_run_limit_cents: float = 100.00
    alert_threshold_pct: float = 0.80
    hard_stop_threshold_pct: float = 1.00
    allowed_models: List[str] = field(default_factory=lambda: ["gpt-4o", "gpt-4o-mini"])
    max_monthly_runs: int = 1000


class BudgetManager:
    """Manages per-tenant AI budget limits, alerts, and hard stops."""

    def __init__(self, session=None) -> None:
        self._session = session
        self._budgets: dict[str, TenantAIBudget] = {}

    async def get_budget(self, tenant_id: UUID) -> TenantAIBudget:
        key = str(tenant_id)
        if key in self._budgets:
            return self._budgets[key]
        return TenantAIBudget(tenant_id=tenant_id)

    async def check_budget(self, tenant_id: UUID, estimated_cost_cents: float) -> dict:
        budget = await self.get_budget(tenant_id)
        monthly = await self._get_monthly_spend(tenant_id)
        daily = await self._get_daily_spend(tenant_id)

        monthly_pct = monthly / budget.monthly_limit_cents if budget.monthly_limit_cents > 0 else 0
        daily_pct = daily / budget.daily_limit_cents if budget.daily_limit_cents > 0 else 0

        allowed = True
        alert_level = None

        if monthly_pct >= budget.hard_stop_threshold_pct or daily_pct >= budget.hard_stop_threshold_pct:
            allowed = False
            alert_level = "critical"
        elif monthly_pct >= budget.alert_threshold_pct or daily_pct >= budget.alert_threshold_pct:
            alert_level = "warning"

        return {
            "allowed": allowed,
            "alert_level": alert_level,
            "monthly_usage_pct": monthly_pct * 100,
            "daily_usage_pct": daily_pct * 100,
            "monthly_remaining_cents": max(0, budget.monthly_limit_cents - monthly),
            "daily_remaining_cents": max(0, budget.daily_limit_cents - daily),
        }

    async def _get_monthly_spend(self, tenant_id: UUID) -> float:
        return 0.0  # In production, query ai_cost_ledger

    async def _get_daily_spend(self, tenant_id: UUID) -> float:
        return 0.0

    def set_budget(self, budget: TenantAIBudget) -> None:
        self._budgets[str(budget.tenant_id)] = budget