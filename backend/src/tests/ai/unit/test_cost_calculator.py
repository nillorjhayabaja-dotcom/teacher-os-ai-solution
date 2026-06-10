"""Unit tests for Cost Calculator."""

import pytest
from backend.src.domains.ai.services.cost_calculator import CostCalculator, PRICING_TABLE


class TestCostCalculator:
    def setup_method(self):
        self.calc = CostCalculator()

    def test_gpt4o_cost(self):
        cost = self.calc.calculate("gpt-4o", "openai", prompt_tokens=1000, completion_tokens=500)
        assert cost.model == "gpt-4o"
        assert cost.provider == "openai"
        assert cost.total_cost_cents > 0

    def test_gpt4o_mini_cost(self):
        cost = self.calc.calculate("gpt-4o-mini", "openai", prompt_tokens=1000, completion_tokens=500)
        assert cost.total_cost_cents > 0

    def test_cached_tokens_reduce_cost(self):
        cost_no_cache = self.calc.calculate("gpt-4o", "openai", prompt_tokens=1000, completion_tokens=500, cached_tokens=0)
        cost_with_cache = self.calc.calculate("gpt-4o", "openai", prompt_tokens=1000, completion_tokens=500, cached_tokens=500)
        assert cost_with_cache.total_cost_cents < cost_no_cache.total_cost_cents

    def test_zero_tokens(self):
        cost = self.calc.calculate("gpt-4o", "openai", prompt_tokens=0, completion_tokens=0)
        assert cost.total_cost_cents == 0.0

    def test_unknown_model_uses_default(self):
        cost = self.calc.calculate("unknown-model", "openai", prompt_tokens=1000, completion_tokens=500)
        assert cost.total_cost_cents > 0

    def test_pricing_table_completeness(self):
        assert "gpt-4o" in PRICING_TABLE
        assert "gpt-4o-mini" in PRICING_TABLE
        assert "claude-3.5-sonnet" in PRICING_TABLE