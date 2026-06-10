"""AI Agents API — FastAPI router for /api/v1/ai/agents with proper dependency injection."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/ai/agents", tags=["ai-agents"])


class AgentSummary(BaseModel):
    kind: str
    name: str
    description: str
    risk_level: str
    supports_streaming: bool
    supports_conversation: bool
    default_model: str
    required_tools: List[str] = []


class AgentListResponse(BaseModel):
    agents: List[AgentSummary]
    total: int


class AgentRunRequest(BaseModel):
    domain_data: Dict[str, Any] = Field(..., description="Domain-specific input payload")
    conversation_id: Optional[UUID] = None
    model_override: Optional[str] = None
    temperature_override: Optional[float] = Field(None, ge=0, le=2)
    max_tokens_override: Optional[int] = Field(None, ge=1, le=16384)
    context: Optional[Dict[str, Any]] = None


class AgentRunResponse(BaseModel):
    run_id: str
    status: str
    agent_kind: str
    output: Optional[Dict[str, Any]] = None
    review_state: Optional[str] = None
    cost_cents: Optional[float] = None
    latency_ms: Optional[int] = None
    token_usage: Optional[Dict[str, int]] = None


def _build_runner_components():
    """Build production or test components based on environment."""
    from backend.src.infrastructure.ai.agent_registry import AgentRegistry
    from backend.src.infrastructure.ai.tools.tool_registry import ToolRegistry
    from backend.src.infrastructure.ai.prompts.prompt_registry import PromptRegistry
    from backend.src.infrastructure.ai.cost.budget_manager import BudgetManager
    from backend.src.infrastructure.ai.security.prompt_guard import PromptInjectionGuard
    from backend.src.domains.ai.services.cost_calculator import CostCalculator
    from backend.src.domains.ai.services.review_gate import AIReviewGate
    from backend.src.domains.ai.services.agent_runner import AgentRunner
    from backend.src.application.ai.run_agent_use_case import RunAgentUseCase

    # Use OpenAI provider in production, Fake provider in development/test
    if os.getenv("OPENAI_API_KEY"):
        from backend.src.infrastructure.ai.providers.openai_provider import OpenAIProvider
        llm = OpenAIProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
    else:
        from backend.src.infrastructure.ai.providers.fake_provider import FakeLLMProvider
        llm = FakeLLMProvider()

    registry = AgentRegistry()
    prompts = PromptRegistry()
    tools = ToolRegistry()
    runner = AgentRunner(
        llm_provider=llm,
        prompt_registry=prompts,
        tool_registry=tools,
        cost_calculator=CostCalculator(),
    )
    review_gate = AIReviewGate(agent_registry=registry)
    budget = BudgetManager()
    guard = PromptInjectionGuard()

    use_case = RunAgentUseCase(
        agent_registry=registry,
        agent_runner=runner,
        review_gate=review_gate,
        budget_manager=budget,
        prompt_guard=guard,
    )
    return use_case, registry


@router.get("", response_model=AgentListResponse)
async def list_agents():
    """List all available AI agents."""
    _use_case, registry = _build_runner_components()
    agents = registry.list_agents()
    return AgentListResponse(
        agents=[
            AgentSummary(
                kind=a.kind.value,
                name=a.name,
                description=a.description,
                risk_level=a.risk_level,
                supports_streaming=a.supports_streaming,
                supports_conversation=a.supports_conversation,
                default_model=a.default_model.model_name,
                required_tools=a.required_tools,
            )
            for a in agents
        ],
        total=len(agents),
    )


@router.get("/{kind}")
async def get_agent(kind: str):
    """Get details of a specific agent including output schema."""
    _use_case, registry = _build_runner_components()
    agent = registry.get_or_none(kind)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {kind}")
    return {
        "kind": agent.kind.value,
        "name": agent.name,
        "description": agent.description,
        "risk_level": agent.risk_level,
        "default_model": agent.default_model.to_dict(),
        "required_tools": agent.required_tools,
        "optional_tools": agent.optional_tools,
        "supports_streaming": agent.supports_streaming,
        "supports_conversation": agent.supports_conversation,
        "max_input_tokens": agent.max_input_tokens,
        "output_schema": agent.get_output_schema(),
    }


@router.post("/{kind}/run", response_model=AgentRunResponse)
async def run_agent(kind: str, request: AgentRunRequest):
    """Execute an AI agent with full pipeline: security → budget → RAG → LLM → review."""
    use_case, _registry = _build_runner_components()

    result = await use_case.execute(
        agent_kind=kind,
        tenant_id=request.context.get("tenant_id", UUID(int=0)) if request.context else UUID(int=0),
        user_id=request.context.get("user_id", UUID(int=0)) if request.context else UUID(int=0),
        domain_data=request.domain_data,
        model_override=request.model_override,
        temperature_override=request.temperature_override,
        max_tokens_override=request.max_tokens_override,
        conversation_id=request.conversation_id,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return AgentRunResponse(
        run_id=result.get("run_id", ""),
        status=result.get("status", "unknown"),
        agent_kind=result.get("agent_kind", kind),
        output=result.get("output"),
        review_state=result.get("review_state"),
        cost_cents=result.get("cost_cents"),
        latency_ms=result.get("latency_ms"),
        token_usage=result.get("token_usage"),
    )