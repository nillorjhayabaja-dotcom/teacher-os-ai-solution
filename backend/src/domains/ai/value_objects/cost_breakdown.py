"""Cost breakdown value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostBreakdown:
    """Cost tracking for a single AI run."""

    input_cost_cents: float
    output_cost_cents: float
    total_cost_cents: float
    model: str
    provider: str
    currency: str = "USD"

    def to_dict(self) -> dict:
        return {
            "input_cost_cents": self.input_cost_cents,
            "output_cost_cents": self.output_cost_cents,
            "total_cost_cents": self.total_cost_cents,
            "model": self.model,
            "provider": self.provider,
            "currency": self.currency,
        }