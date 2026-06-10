"""AI SQLAlchemy ORM models — maps to the ai.* database schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

# In production, these would use SQLAlchemy declarative_base.
# Placeholder dataclasses for MVP.


def _uuid():
    return str(uuid4())


class AIConversationModel:
    __tablename__ = "ai_conversations"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", _uuid())
        self.tenant_id = kwargs.get("tenant_id")
        self.agent_kind = kwargs.get("agent_kind")
        self.user_id = kwargs.get("user_id")
        self.title = kwargs.get("title")
        self.status = kwargs.get("status", "active")
        self.message_count = kwargs.get("message_count", 0)
        self.total_tokens = kwargs.get("total_tokens", 0)
        self.total_cost_cents = kwargs.get("total_cost_cents", 0.0)
        self.domain_type = kwargs.get("domain_type")
        self.domain_id = kwargs.get("domain_id")
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.updated_at = kwargs.get("updated_at", datetime.utcnow())
        self.deleted_at = kwargs.get("deleted_at")
        self.metadata_ = kwargs.get("metadata_", {})


class AIMessageModel:
    __tablename__ = "ai_messages"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", _uuid())
        self.conversation_id = kwargs.get("conversation_id")
        self.tenant_id = kwargs.get("tenant_id")
        self.role = kwargs.get("role")
        self.content = kwargs.get("content")
        self.tool_calls = kwargs.get("tool_calls", [])
        self.tool_call_id = kwargs.get("tool_call_id")
        self.prompt_tokens = kwargs.get("prompt_tokens", 0)
        self.completion_tokens = kwargs.get("completion_tokens", 0)
        self.model_used = kwargs.get("model_used")
        self.cost_cents = kwargs.get("cost_cents", 0.0)
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.metadata_ = kwargs.get("metadata_", {})


class AIKnowledgeChunkModel:
    __tablename__ = "ai_knowledge_chunks"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", _uuid())
        self.tenant_id = kwargs.get("tenant_id")
        self.content = kwargs.get("content")
        self.embedding = kwargs.get("embedding")
        self.knowledge_type = kwargs.get("knowledge_type", "general")
        self.source_type = kwargs.get("source_type", "manual")
        self.source_id = kwargs.get("source_id")
        self.chunk_index = kwargs.get("chunk_index", 0)
        self.token_count = kwargs.get("token_count", 0)
        self.title = kwargs.get("title")
        self.tags = kwargs.get("tags", [])
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.updated_at = kwargs.get("updated_at", datetime.utcnow())
        self.deleted_at = kwargs.get("deleted_at")
        self.metadata_ = kwargs.get("metadata_", {})


class AIAgentRunModel:
    __tablename__ = "agent_runs"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", _uuid())
        self.tenant_id = kwargs.get("tenant_id")
        self.agent_kind = kwargs.get("agent_kind")
        self.agent_id = kwargs.get("agent_id")
        self.prompt_id = kwargs.get("prompt_id")
        self.prompt_version_id = kwargs.get("prompt_version_id")
        self.user_id = kwargs.get("user_id")
        self.input_context = kwargs.get("input_context", {})
        self.input_hash = kwargs.get("input_hash")
        self.status = kwargs.get("status", "queued")
        self.output_id = kwargs.get("output_id")
        self.raw_response = kwargs.get("raw_response")
        self.parsed_output = kwargs.get("parsed_output")
        self.model_used = kwargs.get("model_used", "")
        self.provider = kwargs.get("provider", "")
        self.prompt_tokens = kwargs.get("prompt_tokens", 0)
        self.completion_tokens = kwargs.get("completion_tokens", 0)
        self.total_tokens = kwargs.get("total_tokens", 0)
        self.cached_tokens = kwargs.get("cached_tokens", 0)
        self.cost_cents = kwargs.get("cost_cents", 0.0)
        self.latency_ms = kwargs.get("latency_ms")
        self.llm_latency_ms = kwargs.get("llm_latency_ms")
        self.error_type = kwargs.get("error_type")
        self.error_message = kwargs.get("error_message")
        self.retry_count = kwargs.get("retry_count", 0)
        self.max_retries = kwargs.get("max_retries", 3)
        self.conversation_id = kwargs.get("conversation_id")
        self.correlation_id = kwargs.get("correlation_id")
        self.request_id = kwargs.get("request_id")
        self.started_at = kwargs.get("started_at")
        self.completed_at = kwargs.get("completed_at")
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.updated_at = kwargs.get("updated_at", datetime.utcnow())
        self.deleted_at = kwargs.get("deleted_at")


class AIOutputModel:
    __tablename__ = "ai_outputs"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", _uuid())
        self.tenant_id = kwargs.get("tenant_id")
        self.run_id = kwargs.get("run_id")
        self.agent_kind = kwargs.get("agent_kind")
        self.payload = kwargs.get("payload", {})
        self.output_version = kwargs.get("output_version", 1)
        self.supersedes_id = kwargs.get("supersedes_id")
        self.supersession_reason = kwargs.get("supersession_reason")
        self.review_state = kwargs.get("review_state", "pending")
        self.reviewed_by = kwargs.get("reviewed_by")
        self.reviewed_at = kwargs.get("reviewed_at")
        self.review_notes = kwargs.get("review_notes")
        self.domain_type = kwargs.get("domain_type")
        self.domain_id = kwargs.get("domain_id")
        self.model_used = kwargs.get("model_used", "")
        self.provider = kwargs.get("provider", "")
        self.prompt_version_id = kwargs.get("prompt_version_id")
        self.system_prompt_hash = kwargs.get("system_prompt_hash")
        self.input_hash = kwargs.get("input_hash")
        self.cost_cents = kwargs.get("cost_cents", 0.0)
        self.token_usage = kwargs.get("token_usage", {})
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.updated_at = kwargs.get("updated_at", datetime.utcnow())
        self.created_by = kwargs.get("created_by")
        self.deleted_at = kwargs.get("deleted_at")
        self.metadata_ = kwargs.get("metadata_", {})