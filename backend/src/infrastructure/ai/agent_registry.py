"""Agent Registry — central registry for all AI agents."""

from __future__ import annotations

from typing import Dict, Optional

from backend.src.domains.ai.agents import (
    AssessmentAgent,
    CommunicationAgent,
    FormsAgent,
    GradebookAgent,
    LessonPlanningAgent,
    ReportAgent,
    StudentRiskAgent,
)
from backend.src.domains.ai.agents.base_agent import BaseAgent


class AgentRegistry:
    """Central registry for all AI agents.

    Registered as a singleton in the DI container. Domain services
    resolve agents by kind.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        for agent_cls in [
            LessonPlanningAgent,
            AssessmentAgent,
            GradebookAgent,
            FormsAgent,
            StudentRiskAgent,
            ReportAgent,
            CommunicationAgent,
        ]:
            agent = agent_cls()
            self._agents[agent.kind.value] = agent

    def get(self, kind: str) -> BaseAgent:
        if kind not in self._agents:
            raise KeyError(f"Agent not found: {kind}")
        return self._agents[kind]

    def get_or_none(self, kind: str) -> Optional[BaseAgent]:
        return self._agents.get(kind)

    def list_agents(self) -> list[BaseAgent]:
        return list(self._agents.values())

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.kind.value] = agent