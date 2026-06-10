"""Agent Runner — orchestrates agent execution with RAG, tools, cost tracking, and persistence."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..agents.base_agent import BaseAgent
from ..value_objects import AIInputContext, CostBreakdown, ModelConfig, RunStatus, TokenUsage
from ..events import AIRunCompleted, AIRunFailed, AIRunStarted, AIToolExecuted


class AgentRunner:
    """Orchestrates the full lifecycle of an AI agent run.

    Handles: prompt loading → RAG retrieval → LLM call → parsing →
    cost tracking → output creation → persistence.
    """

    def __init__(
        self,
        llm_provider,
        prompt_registry,
        vector_store=None,
        working_memory=None,
        tool_registry=None,
        event_bus=None,
        cost_calculator=None,
        run_repo=None,
        output_repo=None,
        metrics_collector=None,
    ) -> None:
        self._llm = llm_provider
        self._prompts = prompt_registry
        self._vector_store = vector_store
        self._working_memory = working_memory
        self._tools = tool_registry
        self._event_bus = event_bus
        self._cost_calc = cost_calculator
        self._run_repo = run_repo
        self._output_repo = output_repo
        self._metrics = metrics_collector

    async def run_agent(
        self,
        agent: BaseAgent,
        context: AIInputContext,
        *,
        model_override: Optional[str] = None,
        temperature_override: Optional[float] = None,
        max_tokens_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        run_id = uuid.uuid4()
        start_time = time.monotonic()
        llm_start_time = 0.0
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        cached_tokens = 0

        # Publish run started event
        if self._event_bus:
            await self._event_bus.publish(AIRunStarted(
                run_id=run_id,
                agent_kind=agent.kind.value,
                tenant_id=context.tenant_id,
                user_id=context.user_id,
            ))

        # Track run in repository
        if self._run_repo:
            await self._run_repo.create({
                "id": run_id,
                "tenant_id": context.tenant_id,
                "agent_kind": agent.kind.value,
                "user_id": context.user_id,
                "status": RunStatus.RUNNING.value,
                "input_context": {
                    "domain_data": context.domain_data,
                    "conversation_history": context.conversation_history[:5] if context.conversation_history else [],
                    "rag_context_count": len(context.rag_context) if context.rag_context else 0,
                },
                "started_at": datetime.now(timezone.utc),
            })

        try:
            # 1. Validate input
            await agent.validate_input(context)

            # 2. RAG retrieval
            rag_query = await agent.get_rag_query(context)
            if rag_query and self._vector_store:
                rag_start = time.monotonic()
                rag_results = await self._vector_store.search(
                    query=rag_query,
                    tenant_id=context.tenant_id,
                    top_k=10,
                )
                rag_latency = int((time.monotonic() - rag_start) * 1000)

                context = AIInputContext(
                    tenant_id=context.tenant_id,
                    agent_kind=context.agent_kind,
                    user_id=context.user_id,
                    domain_data=context.domain_data,
                    conversation_history=context.conversation_history,
                    rag_context=rag_results,
                    additional_context=context.additional_context,
                )

            # 3. Load prompt version
            prompt_version = await self._prompts.get_active_version(
                agent_kind=agent.kind.value,
                category="system",
            )
            prompt_version_id = uuid.UUID(prompt_version["id"]) if prompt_version else uuid.uuid4()

            # 4. Build messages
            messages = await agent.build_messages(context, prompt_version_id)

            # 5. Execute LLM call
            model_config = agent.default_model
            if model_override:
                model_config = ModelConfig(
                    provider=model_config.provider,
                    model_name=model_override,
                    temperature=temperature_override or model_config.temperature,
                    max_tokens=max_tokens_override or model_config.max_tokens,
                    top_p=model_config.top_p,
                    stop_sequences=model_config.stop_sequences,
                    timeout_seconds=model_config.timeout_seconds,
                    retry_attempts=model_config.retry_attempts,
                    fallback_model=model_config.fallback_model,
                )

            llm_start_time = time.monotonic()
            raw_response = await self._llm.chat(messages, model_config)
            llm_latency = int((time.monotonic() - llm_start_time) * 1000)

            # 6. Parse and validate
            output = await agent.parse_response(raw_response, context)

            # 7. Post-process
            output = await agent.post_process(output, context)

            # 8. Compute cost
            latency_ms = int((time.monotonic() - start_time) * 1000)
            # Estimate token counts from the response if provider doesn't return them
            prompt_tokens = len(json.dumps(messages)) // 4  # rough estimate
            completion_tokens = len(raw_response) // 4
            total_tokens = prompt_tokens + completion_tokens

            token_usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cached_tokens=0,
            )
            cost_cents = 0.0

            if self._cost_calc:
                cost = self._cost_calc.calculate(
                    model=model_config.model_name,
                    provider=model_config.provider,
                    prompt_tokens=token_usage.prompt_tokens,
                    completion_tokens=token_usage.completion_tokens,
                    cached_tokens=token_usage.cached_tokens,
                )
                cost_cents = cost.total_cost_cents

            # 9. Build result
            result = {
                "run_id": str(run_id),
                "status": RunStatus.COMPLETED.value,
                "agent_kind": agent.kind.value,
                "output": output,
                "token_usage": token_usage.to_dict(),
                "cost_cents": cost_cents,
                "latency_ms": latency_ms,
                "llm_latency_ms": llm_latency,
                "model_used": model_config.model_name,
                "provider": model_config.provider,
            }

            # 10. Update run repository
            if self._run_repo:
                await self._run_repo.update(run_id, {
                    "status": RunStatus.COMPLETED.value,
                    "output": output,
                    "raw_response": raw_response[:10000],  # truncate to avoid bloat
                    "model_used": model_config.model_name,
                    "provider": model_config.provider,
                    "prompt_tokens": token_usage.prompt_tokens,
                    "completion_tokens": token_usage.completion_tokens,
                    "total_tokens": token_usage.total_tokens,
                    "cached_tokens": token_usage.cached_tokens,
                    "cost_cents": cost_cents,
                    "latency_ms": latency_ms,
                    "llm_latency_ms": llm_latency,
                    "completed_at": datetime.now(timezone.utc),
                })

            # 11. Publish completed event
            if self._event_bus:
                output_id = uuid.uuid4()
                await self._event_bus.publish(AIRunCompleted(
                    run_id=run_id,
                    agent_kind=agent.kind.value,
                    tenant_id=context.tenant_id,
                    user_id=context.user_id,
                    output_id=output_id,
                    token_usage=token_usage.to_dict(),
                    cost_cents=cost_cents,
                    latency_ms=latency_ms,
                ))

            # 12. Record metrics
            if self._metrics:
                self._metrics.record_run(
                    agent_kind=agent.kind.value,
                    status="completed",
                    model=model_config.model_name,
                    tenant_id=str(context.tenant_id),
                    latency_ms=latency_ms,
                    cost_cents=cost_cents,
                    prompt_tokens=token_usage.prompt_tokens,
                    completion_tokens=token_usage.completion_tokens,
                )

            return result

        except Exception as e:
            latency_ms = int((time.monotonic() - start_time) * 1000)
            error_type = type(e).__name__

            # Update run with failure
            if self._run_repo:
                await self._run_repo.update(run_id, {
                    "status": RunStatus.FAILED.value,
                    "error_type": error_type,
                    "error_message": str(e)[:1000],
                    "latency_ms": latency_ms,
                    "completed_at": datetime.now(timezone.utc),
                })

            if self._event_bus:
                await self._event_bus.publish(AIRunFailed(
                    run_id=run_id,
                    agent_kind=agent.kind.value,
                    tenant_id=context.tenant_id,
                    user_id=context.user_id,
                    error_type=error_type,
                    error_message=str(e),
                    retry_count=0,
                ))

            if self._metrics:
                self._metrics.record_error(
                    agent_kind=agent.kind.value,
                    error_type=error_type,
                    tenant_id=str(context.tenant_id),
                )

            return {
                "run_id": str(run_id),
                "status": RunStatus.FAILED.value,
                "agent_kind": agent.kind.value,
                "error_type": error_type,
                "error_message": str(e),
                "latency_ms": latency_ms,
            }

    async def run_agent_with_tools(
        self,
        agent: BaseAgent,
        context: AIInputContext,
        *,
        model_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run agent with tool execution support during LLM calls."""
        run_id = uuid.uuid4()
        start_time = time.monotonic()

        if self._event_bus:
            await self._event_bus.publish(AIRunStarted(
                run_id=run_id, agent_kind=agent.kind.value,
                tenant_id=context.tenant_id, user_id=context.user_id,
            ))

        try:
            tool_schemas = []
            if self._tools:
                all_tool_names = agent.required_tools + agent.optional_tools
                tool_schemas = self._tools.get_schemas_for_agent(all_tool_names)

            # Build messages and execute LLM with tool schemas
            prompt_version = await self._prompts.get_active_version(agent.kind.value, "system")
            prompt_version_id = uuid.UUID(prompt_version["id"]) if prompt_version else uuid.uuid4()
            messages = await agent.build_messages(context, prompt_version_id)
            result = await self._run_with_tool_loop(
                agent, context, messages, tool_schemas, run_id,
            )

            latency_ms = int((time.monotonic() - start_time) * 1000)
            result["run_id"] = str(run_id)
            result["latency_ms"] = latency_ms

            if self._event_bus:
                await self._event_bus.publish(AIRunCompleted(
                    run_id=run_id, agent_kind=agent.kind.value,
                    tenant_id=context.tenant_id, user_id=context.user_id,
                    output_id=uuid.uuid4(), token_usage=result.get("token_usage", {}),
                    cost_cents=result.get("cost_cents", 0), latency_ms=latency_ms,
                ))

            return result

        except Exception as e:
            latency_ms = int((time.monotonic() - start_time) * 1000)
            if self._event_bus:
                await self._event_bus.publish(AIRunFailed(
                    run_id=run_id, agent_kind=agent.kind.value,
                    tenant_id=context.tenant_id, user_id=context.user_id,
                    error_type=type(e).__name__, error_message=str(e), retry_count=0,
                ))
            return {
                "run_id": str(run_id), "status": RunStatus.FAILED.value,
                "error_type": type(e).__name__, "error_message": str(e),
                "latency_ms": latency_ms,
            }

    async def _run_with_tool_loop(
        self, agent, context, messages, tool_schemas, run_id,
    ) -> Dict[str, Any]:
        """Execute LLM with function-calling loop for tool execution."""
        max_iterations = 10
        current_messages = list(messages)

        for iteration in range(max_iterations):
            raw_response = await self._llm.chat(current_messages, agent.default_model)
            current_messages.append({"role": "assistant", "content": raw_response})

            # Check if response contains tool calls
            tool_call_start = raw_response.find("{" + '"name"')
            if tool_call_start == -1:
                # No tool calls, agent's final response
                output = await agent.parse_response(raw_response, context)
                output = await agent.post_process(output, context)
                total_tokens = sum(len(json.dumps(m)) // 4 for m in current_messages) + len(raw_response) // 4
                return {
                    "status": RunStatus.COMPLETED.value,
                    "output": output,
                    "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": total_tokens},
                    "cost_cents": 0.0,
                    "model_used": agent.default_model.model_name,
                    "provider": agent.default_model.provider,
                    "iterations": iteration,
                }

            # Parse and execute tool calls
            try:
                tool_call = json.loads(raw_response[raw_response.find("{"):raw_response.rfind("}") + 1])
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("arguments", {})
            except (json.JSONDecodeError, ValueError):
                continue

            if self._tools:
                tool = self._tools.get(tool_name)
                if tool:
                    tool_result = await tool.execute(
                        arguments=tool_args,
                        tenant_id=context.tenant_id,
                        user_id=context.user_id,
                        run_id=run_id,
                    )
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_name,
                        "content": json.dumps(tool_result),
                    })

                    if self._event_bus:
                        await self._event_bus.publish(AIToolExecuted(
                            execution_id=uuid.uuid4(), run_id=run_id,
                            tool_name=tool_name, tenant_id=context.tenant_id,
                            success=True, latency_ms=0,
                        ))

        # Fallback: return last response if max iterations reached
        return {
            "status": RunStatus.COMPLETED.value,
            "output": {"warning": "Max tool iterations reached", "raw_content": raw_response},
            "token_usage": {}, "cost_cents": 0.0,
            "model_used": agent.default_model.model_name,
            "provider": agent.default_model.provider,
            "iterations": max_iterations,
        }