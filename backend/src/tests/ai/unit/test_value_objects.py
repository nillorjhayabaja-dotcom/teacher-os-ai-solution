"""Unit tests for AI value objects."""

import pytest
from backend.src.domains.ai.value_objects import (
    AgentKind,
    CostBreakdown,
    ModelConfig,
    ReviewState,
    RunStatus,
    TokenUsage,
    AIInputContext,
    OutputSupersessionReason,
)
from uuid import uuid4


class TestAgentKind:
    def test_mvp_kinds_count(self):
        assert len(AgentKind.mvp_kinds()) == 7

    def test_all_kinds_count(self):
        assert len(list(AgentKind)) == 12

    def test_display_name(self):
        assert AgentKind.LESSON_PLANNING.display_name == "Lesson Planning"

    def test_string_value(self):
        assert AgentKind.ASSESSMENT.value == "assessment"


class TestTokenUsage:
    def test_creation(self):
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.cached_tokens == 0

    def test_cache_hit_rate(self):
        usage = TokenUsage(prompt_tokens=200, completion_tokens=100, total_tokens=300, cached_tokens=50)
        assert usage.cache_hit_rate == 0.25

    def test_cache_hit_rate_zero_tokens(self):
        usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        assert usage.cache_hit_rate == 0.0

    def test_to_dict(self):
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30, cached_tokens=5)
        d = usage.to_dict()
        assert d["prompt_tokens"] == 10
        assert d["cached_tokens"] == 5

    def test_from_dict(self):
        usage = TokenUsage.from_dict({"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30})
        assert usage.prompt_tokens == 10


class TestModelConfig:
    def test_creation(self):
        config = ModelConfig(provider="openai", model_name="gpt-4o")
        assert config.provider == "openai"
        assert config.temperature == 0.7

    def test_to_dict(self):
        config = ModelConfig(provider="openai", model_name="gpt-4o", temperature=0.5)
        d = config.to_dict()
        assert d["provider"] == "openai"
        assert d["temperature"] == 0.5

    def test_from_dict(self):
        config = ModelConfig.from_dict({"provider": "openai", "model_name": "gpt-4o"})
        assert config.model_name == "gpt-4o"


class TestCostBreakdown:
    def test_creation(self):
        cost = CostBreakdown(
            input_cost_cents=0.25, output_cost_cents=1.00,
            total_cost_cents=1.25, model="gpt-4o", provider="openai",
        )
        assert cost.total_cost_cents == 1.25
        assert cost.currency == "USD"


class TestReviewState:
    def test_states(self):
        assert ReviewState.PENDING.value == "pending"
        assert ReviewState.APPROVED.value == "approved"
        assert ReviewState.AUTO_APPROVED.value == "auto_approved"


class TestRunStatus:
    def test_statuses(self):
        assert RunStatus.QUEUED.value == "queued"
        assert RunStatus.COMPLETED.value == "completed"
        assert RunStatus.FAILED.value == "failed"


class TestAIInputContext:
    def test_creation(self):
        ctx = AIInputContext(
            tenant_id=uuid4(), agent_kind="lesson_planning",
            user_id=uuid4(), domain_data={"subject": "Math"},
        )
        assert ctx.agent_kind == "lesson_planning"
        assert ctx.rag_context == []
        assert ctx.conversation_history == []