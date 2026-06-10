"""Cost Calculator — computes AI run costs based on provider pricing."""

from __future__ import annotations

from ..value_objects import CostBreakdown

# Pricing in cents per 1M tokens
PRICING_TABLE = {
    "gpt-4o": {"input": 0.25, "output": 1.00, "cached_input": 0.125},
    "gpt-4o-mini": {"input": 0.015, "output": 0.06, "cached_input": 0.0075},
    "claude-3.5-sonnet": {"input": 0.30, "output": 1.50, "cached_input": 0.03},
    "claude-3-haiku": {"input": 0.025, "output": 0.125, "cached_input": 0.003},
}


class CostCalculator:
    """Calculates cost for AI runs based on token usage and model pricing."""

    def calculate(
        self,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
    ) -> CostBreakdown:
        pricing = PRICING_TABLE.get(model, {"input": 0.25, "output": 1.00, "cached_input": 0.125})

        # Compute input cost (subtract cached tokens from regular input pricing)
        regular_input_tokens = max(0, prompt_tokens - cached_tokens)
        input_cost = (regular_input_tokens * pricing["input"] / 1_000_000)
        cached_cost = (cached_tokens * pricing["cached_input"] / 1_000_000) if cached_tokens > 0 else 0
        total_input_cost = input_cost + cached_cost

        output_cost = (completion_tokens * pricing["output"] / 1_000_000)
        total_cost = total_input_cost + output_cost

        return CostBreakdown(
            input_cost_cents=round(total_input_cost, 6),
            output_cost_cents=round(output_cost, 6),
            total_cost_cents=round(total_cost, 6),
            model=model,
            provider=provider,
        )