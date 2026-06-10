# TeacherOS — AI Platform Architecture

> **Document Purpose:** Source of truth for all AI implementations in TeacherOS.
> **Author:** Principal AI Systems Architect & Enterprise Software Architect
> **Target Stack:** PostgreSQL 15+ (pgvector), FastAPI, Redis, Celery, Python 3.12+
> **Status:** v1.0 — Ready for MVP Implementation
> **Last Updated:** 2026-06-09

---

## Table of Contents

1. [AI Bounded Context](#1-ai-bounded-context)
2. [AI Domain Model](#2-ai-domain-model)
3. [Agent Registry Architecture](#3-agent-registry-architecture)
4. [Tool Registry Architecture](#4-tool-registry-architecture)
5. [Prompt Registry Architecture](#5-prompt-registry-architecture)
6. [Memory Architecture](#6-memory-architecture)
7. [RAG Architecture](#7-rag-architecture)
8. [AI Workflow Engine](#8-ai-workflow-engine)
9. [AI Security Model](#9-ai-security-model)
10. [Multi-Tenant Isolation Strategy](#10-multi-tenant-isolation-strategy)
11. [Cost Tracking System](#11-cost-tracking-system)
12. [Observability Architecture](#12-observability-architecture)
13. [Event Architecture](#13-event-architecture)
14. [Database Schema](#14-database-schema)
15. [API Contracts](#15-api-contracts)
16. [WebSocket Contracts](#16-websocket-contracts)
17. [Folder Structure](#17-folder-structure)
18. [Sequence Diagrams](#18-sequence-diagrams)
19. [Deployment Architecture](#19-deployment-architecture)
20. [Testing Strategy](#20-testing-strategy)

---

## 1. AI Bounded Context

### 1.1 Position in the Domain Map

The AI context is a **cross-cutting bounded context** — like `audit`, it does not own business data. Instead, it:

- **Consumes events** from all domain contexts (academic, assessment, gradebook, forms, intervention, comms, compliance)
- **Produces outputs** that domain services consume via the workflow engine
- **Never writes directly** to domain tables; it writes to `ai.*` schema tables and emits events

```
┌─────────────────────────────────────────────────────────────────┐
│                    TeacherOS Bounded Contexts                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Identity │  │   SIS    │  │ Academic │  │Assessment│       │
│  │ (core)   │  │  (sis)   │  │(academic)│  │(assess.) │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │             │
│       │         ┌────▼──────────────▼──────────────▼────┐       │
│       │         │            Event Bus                   │       │
│       │         │   (audit.domain_events + Redis)        │       │
│       │         └────┬──────────────┬──────────────┬────┘       │
│       │              │              │              │             │
│  ┌────▼─────┐  ┌─────▼────┐  ┌─────▼────┐  ┌─────▼────┐       │
│  │ Gradebook│  │  Forms   │  │ Interven.│  │  Comms   │       │
│  │(gradeb.) │  │ (forms)  │  │(interv.) │  │ (comms)  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │             │
│       └──────────────┼──────────────┼──────────────┘             │
│                      │              │                            │
│              ┌───────▼──────────────▼───────┐                   │
│              │       AI / Agents            │                   │
│              │         (ai)                  │                   │
│              │  • Consumes domain events     │                   │
│              │  • Produces AI outputs        │                   │
│              │  • Writes back via workflow   │                   │
│              └───────────────┬───────────────┘                   │
│                              │                                  │
│              ┌───────────────▼───────────────┐                   │
│              │     Workflow Engine           │                   │
│              │        (workflow)             │                   │
│              │  • Orchestrates AI → Domain   │                   │
│              │  • Human-in-the-loop gates    │                   │
│              └───────────────────────────────┘                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Audit & Observability (cross-cutting, read-only)      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Context Map Relationships

| Upstream Context | Downstream (AI) | Relationship | Data Flow |
|---|---|---|---|
| **Academic** | AI | Event Consumer | Lesson plans, MELCs, DLL → AI reads for context |
| **Assessment** | AI | Event Consumer | Quizzes, rubrics, results → AI reads for generation |
| **Gradebook** | AI | Event Consumer | Scores, computed grades → AI reads for risk analysis |
| **SIS** | AI | Event Consumer | Students, attendance, enrollments → AI reads for context |
| **Forms** | AI | Event Consumer | School form templates, data → AI generates forms |
| **Intervention** | AI | Event Consumer | Risk cases, actions → AI suggests interventions |
| **Comms** | AI | Event Consumer | Communication history → AI drafts messages |
| **Compliance** | AI | Event Consumer | RPMS indicators, reports → AI generates reports |
| **AI** | Academic | Event Producer | `ai.output.approved` → Academic applies lesson plan |
| **AI** | Assessment | Event Producer | `ai.output.approved` → Assessment creates items |
| **AI** | Gradebook | Event Producer | `ai.output.approved` → Gradebook applies suggestions |
| **AI** | Forms | Event Producer | `ai.output.approved` → Forms creates form instances |
| **AI** | Intervention | Event Producer | `ai.output.approved` → Intervention creates cases |
| **AI** | Comms | Event Producer | `ai.output.approved` → Comms sends messages |
| **AI** | Compliance | Event Producer | `ai.output.approved` → Compliance creates reports |

### 1.3 Anti-Corruption Layer

```python
# The AI context never imports domain models directly.
# It only knows about domain data through:
# 1. Event payloads (JSON-validated with Pydantic)
# 2. Read-only domain queries via repository interfaces
# 3. Output contracts that domain services consume

class AIAntiCorruptionLayer:
    """Prevents AI context from leaking into domain models."""

    def adapt_domain_event(self, event: BaseDomainEvent) -> AIInputContext:
        """Convert a domain event into AI-consumable context."""
        ...

    def adapt_ai_output(self, output: AIOutput, target_context: str) -> DomainCommand:
        """Convert an AI output into a domain command (via workflow)."""
        ...
```

---

## 2. AI Domain Model

### 2.1 Aggregate Roots

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI Domain Model                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐         ┌─────────────────┐               │
│  │    AIAgent       │◄───────►│   Prompt        │               │
│  │  (aggregate)     │ 1    N │  (aggregate)     │               │
│  │                  │         │                  │               │
│  │  id              │         │  id              │               │
│  │  name            │         │  name            │               │
│  │  kind            │         │  description     │               │
│  │  provider_config │         │  current_version │               │
│  │  model_config    │         │  category        │               │
│  │  tools[]         │         │  is_active       │               │
│  │  is_active       │         │                  │               │
│  └────────┬─────────┘         └────────┬────────┘               │
│           │                            │                        │
│           │ 1                          │ 1                      │
│           │ N                          │ N                      │
│  ┌────────▼─────────┐         ┌────────▼─────────┐               │
│  │   AgentRun       │         │  PromptVersion   │               │
│  │  (aggregate)     │         │  (entity)        │               │
│  │                  │         │                  │               │
│  │  id              │         │  id              │               │
│  │  agent_id        │         │  prompt_id       │               │
│  │  tenant_id       │         │  version_number  │               │
│  │  input_context   │         │  system_prompt   │               │
│  │  status          │         │  user_template   │               │
│  │  token_usage     │         │  few_shot_examples│              │
│  │  cost_cents      │         │  variables[]     │               │
│  │  latency_ms      │         │  metadata        │               │
│  │  error           │         │                  │               │
│  └────────┬─────────┘         └──────────────────┘               │
│           │ 1                                                    │
│           │ N                                                    │
│  ┌────────▼─────────┐         ┌──────────────────┐               │
│  │   AIOutput       │         │   AIFeedback     │               │
│  │  (aggregate)     │◄───────►│  (entity)        │               │
│  │                  │ 1    N │                  │               │
│  │  id              │         │  id              │               │
│  │  run_id          │         │  output_id       │               │
│  │  agent_id        │         │  reviewer_id     │               │
│  │  tenant_id       │         │  rating (1-5)    │               │
│  │  payload (JSONB) │         │  comment         │               │
│  │  review_state    │         │  edited_output   │               │
│  │  supersedes_id   │         │  feedback_type   │               │
│  │  domain_type     │         │  created_at      │               │
│  │  domain_id       │         │                  │               │
│  │  model_used      │         └──────────────────┘               │
│  │  prompt_version  │                                            │
│  │  token_usage     │         ┌──────────────────┐               │
│  │  cost_cents      │         │  AIConversation  │               │
│  └──────────────────┘         │  (aggregate)     │               │
│                               │                  │               │
│                               │  id              │               │
│                               │  tenant_id       │               │
│                               │  agent_id        │               │
│                               │  user_id         │               │
│                               │  title           │               │
│                               │  status          │               │
│                               │  metadata        │               │
│                               └────────┬─────────┘               │
│                                        │ 1                       │
│                                        │ N                       │
│                               ┌────────▼─────────┐               │
│                               │   AIMessage      │               │
│                               │  (entity)        │               │
│                               │                  │               │
│                               │  id              │               │
│                               │  conversation_id │               │
│                               │  role            │               │
│                               │  content         │               │
│                               │  tool_calls[]    │               │
│                               │  token_usage     │               │
│                               │  created_at      │               │
│                               └──────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Value Objects

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class AgentKind(str, Enum):
    """12 specialized agent kinds (7 MVP, 5 post-MVP)."""
    LESSON_PLANNING = "lesson_planning"         # MVP
    ASSESSMENT = "assessment"                    # MVP
    GRADEBOOK = "gradebook"                      # MVP
    FORMS = "forms"                              # MVP
    STUDENT_RISK = "student_risk"                # MVP
    REPORT = "report"                            # MVP
    COMMUNICATION = "communication"              # MVP
    RUBRIC_GENERATION = "rubric_generation"      # Post-MVP
    CURRICULUM_ALIGNMENT = "curriculum_alignment" # Post-MVP
    ATTENDANCE_ANALYSIS = "attendance_analysis"   # Post-MVP
    PARENT_SUMMARY = "parent_summary"            # Post-MVP
    COMPLIANCE_CHECK = "compliance_check"        # Post-MVP


class ReviewState(str, Enum):
    """Human-in-the-loop review lifecycle."""
    PENDING = "pending"          # Generated, awaiting first review
    IN_REVIEW = "in_review"      # Reviewer has started examining
    APPROVED = "approved"        # Human approved the output
    REJECTED = "rejected"        # Human rejected the output
    EDITED = "edited"            # Human edited and approved
    AUTO_APPROVED = "auto_approved"  # Auto-approved (low-risk)


class RunStatus(str, Enum):
    """Agent execution lifecycle."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class OutputSupersessionReason(str, Enum):
    """Why an output was superseded."""
    REGENERATED = "regenerated"      # User requested regeneration
    EDITED = "edited"                # Human edited and created new version
    PROMPT_UPDATED = "prompt_updated"  # Prompt was updated, output regenerated
    CORRECTION = "correction"        # Error correction


@dataclass(frozen=True)
class TokenUsage:
    """Token consumption breakdown for a single LLM call."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached_tokens: int = 0  # Prompt caching savings

    @property
    def cache_hit_rate(self) -> float:
        if self.prompt_tokens == 0:
            return 0.0
        return self.cached_tokens / self.prompt_tokens


@dataclass(frozen=True)
class CostBreakdown:
    """Cost tracking for a single AI run."""
    input_cost_cents: float
    output_cost_cents: float
    total_cost_cents: float
    model: str
    provider: str
    currency: str = "USD"


@dataclass(frozen=True)
class ModelConfig:
    """LLM model configuration for an agent."""
    provider: str              # "openai", "anthropic", "ollama"
    model_name: str            # "gpt-4o", "claude-3.5-sonnet", etc.
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    stop_sequences: tuple = ()
    timeout_seconds: int = 120
    retry_attempts: int = 3
    fallback_model: Optional[str] = None  # Degradation path


@dataclass(frozen=True)
class AIInputContext:
    """Structured input context assembled for an agent run."""
    tenant_id: UUID
    agent_kind: str
    user_id: UUID
    domain_data: Dict[str, Any]        # Domain-specific payload
    conversation_history: List[Dict] = field(default_factory=list)
    rag_context: List[Dict] = field(default_factory=list)  # Retrieved chunks
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIOutputMetadata:
    """Metadata attached to every AI output for provenance."""
    model_used: str
    provider: str
    prompt_version_id: UUID
    system_prompt_hash: str      # SHA-256 of the system prompt used
    input_hash: str              # SHA-256 of the input (dedup detection)
    generation_timestamp: str
    temperature: float
    max_tokens: int
```

### 2.3 Domain Events

```python
from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID

from backend.src.events.base_domain_event import BaseDomainEvent


class AIRunStarted(BaseDomainEvent):
    """Emitted when an agent run begins execution."""
    run_id: UUID
    agent_kind: str
    tenant_id: UUID
    user_id: UUID


class AIRunCompleted(BaseDomainEvent):
    """Emitted when an agent run finishes successfully."""
    run_id: UUID
    agent_kind: str
    tenant_id: UUID
    user_id: UUID
    output_id: UUID
    token_usage: Dict[str, int]
    cost_cents: float
    latency_ms: int


class AIRunFailed(BaseDomainEvent):
    """Emitted when an agent run fails."""
    run_id: UUID
    agent_kind: str
    tenant_id: UUID
    user_id: UUID
    error_type: str
    error_message: str
    retry_count: int


class AIOutputGenerated(BaseDomainEvent):
    """Emitted when a new AI output is created."""
    output_id: UUID
    run_id: UUID
    agent_kind: str
    tenant_id: UUID
    superseded_output_id: Optional[UUID]  # Previous output this replaces


class AIOutputReviewed(BaseDomainEvent):
    """Emitted when a human reviews an AI output."""
    output_id: UUID
    tenant_id: UUID
    reviewer_id: UUID
    review_state: str  # approved, rejected, edited
    feedback_id: Optional[UUID]


class AIFeedbackSubmitted(BaseDomainEvent):
    """Emitted when feedback is submitted on an AI output."""
    feedback_id: UUID
    output_id: UUID
    tenant_id: UUID
    reviewer_id: UUID
    rating: int  # 1-5


class AIBudgetAlert(BaseDomainEvent):
    """Emitted when a tenant approaches or exceeds budget."""
    tenant_id: UUID
    alert_level: str  # "warning" (80%) or "critical" (100%)
    current_spend_cents: float
    budget_limit_cents: float
    period: str  # "monthly", "daily"


class AIToolExecuted(BaseDomainEvent):
    """Emitted when an agent executes a tool."""
    execution_id: UUID
    run_id: UUID
    tool_name: str
    tenant_id: UUID
    success: bool
    latency_ms: int
```

---

## 3. Agent Registry Architecture

### 3.1 Abstract Base Agent

```python
# backend/src/domains/ai/agents/base_agent.py
from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..value_objects import (
    AIInputContext,
    AgentKind,
    CostBreakdown,
    ModelConfig,
    TokenUsage,
)


class BaseAgent(abc.ABC):
    """Abstract base class for all AI agents.

    Every concrete agent implements domain-specific logic while the
    infrastructure layer handles LLM communication, cost tracking,
    and observability.
    """

    # ------------------------------------------------------------------
    # Subclass must define these
    # ------------------------------------------------------------------
    kind: AgentKind
    name: str
    description: str
    default_model: ModelConfig
    required_tools: List[str] = []
    optional_tools: List[str] = []
    max_input_tokens: int = 8000
    supports_streaming: bool = True
    supports_conversation: bool = False
    risk_level: str = "medium"  # "low" | "medium" | "high" — controls auto-approval

    # ------------------------------------------------------------------
    # Core execution interface
    # ------------------------------------------------------------------
    @abc.abstractmethod
    async def build_messages(
        self,
        context: AIInputContext,
        prompt_version_id: UUID,
    ) -> List[Dict[str, str]]:
        """Assemble the message array for the LLM.

        This is where the agent injects system prompts, few-shot examples,
        domain context, and RAG-retrieved content.
        """
        ...

    @abc.abstractmethod
    async def parse_response(
        self,
        raw_response: str,
        context: AIInputContext,
    ) -> Dict[str, Any]:
        """Parse and validate the LLM response into structured output.

        Raises ``InvalidOutputError`` if the response doesn't conform
        to the expected schema.
        """
        ...

    @abc.abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """Return the JSON Schema for this agent's output.

        Used for:
        1. Structured output / function calling
        2. Output validation
        3. API documentation
        """
        ...

    # ------------------------------------------------------------------
    # Optional hooks (subclasses can override)
    # ------------------------------------------------------------------
    async def validate_input(self, context: AIInputContext) -> None:
        """Pre-flight input validation. Raise ``InvalidInputError`` on failure."""
        pass

    async def post_process(
        self,
        output: Dict[str, Any],
        context: AIInputContext,
    ) -> Dict[str, Any]:
        """Post-process the parsed output before persistence.

        Use for: enrichment, cross-referencing, formatting.
        """
        return output

    async def get_rag_query(self, context: AIInputContext) -> Optional[str]:
        """Return a query string for RAG retrieval.

        Override to customize what knowledge is retrieved for this agent.
        Returns None to skip RAG.
        """
        return None

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Return OpenAI-compatible tool/function schemas for this agent."""
        return []
```

### 3.2 Concrete Agent Implementations

```python
# backend/src/domains/ai/agents/lesson_planning_agent.py
from ..value_objects import AgentKind, ModelConfig, AIInputContext
from .base_agent import BaseAgent


class LessonPlanningAgent(BaseAgent):
    kind = AgentKind.LESSON_PLANNING
    name = "Lesson Planning Agent"
    description = "Generates DepEd-aligned lesson plans with objectives, procedure, and activities"
    default_model = ModelConfig(
        provider="openai",
        model_name="gpt-4o",
        temperature=0.7,
        max_tokens=4096,
    )
    required_tools = ["curriculum_search", "melc_lookup"]
    optional_tools = ["student_search", "rubric_generator"]
    risk_level = "medium"  # Requires teacher review

    async def build_messages(self, context, prompt_version_id):
        # 1. Load system prompt from prompt registry
        # 2. Inject MELC context, grade level, subject
        # 3. Inject RAG-retrieved exemplar lesson plans
        # 4. Build few-shot examples
        ...

    async def parse_response(self, raw_response, context):
        # Parse structured JSON: {objectives, procedure, materials, assessment, ...}
        ...

    def get_output_schema(self):
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "grade_level": {"type": "string"},
                "subject": {"type": "string"},
                "learning_objectives": {"type": "array", "items": {"type": "string"}},
                "materials": {"type": "array", "items": {"type": "string"}},
                "procedure": {
                    "type": "object",
                    "properties": {
                        "introductory_activity": {"type": "string"},
                        "main_activity": {"type": "string"},
                        "closing_activity": {"type": "string"},
                    },
                },
                "assessment": {"type": "string"},
                "remarks": {"type": "string"},
            },
            "required": ["title", "learning_objectives", "procedure"],
        }
```

```python
# backend/src/domains/ai/agents/assessment_agent.py
class AssessmentAgent(BaseAgent):
    kind = AgentKind.ASSESSMENT
    name = "Assessment Agent"
    description = "Creates quiz items, rubrics, and formative assessments aligned to MELCs"
    default_model = ModelConfig(provider="openai", model_name="gpt-4o", temperature=0.6)
    required_tools = ["melc_lookup", "rubric_generator"]
    risk_level = "medium"
    # ... implementation
```

```python
# backend/src/domains/ai/agents/student_risk_agent.py
class StudentRiskAgent(BaseAgent):
    kind = AgentKind.STUDENT_RISK
    name = "Student Risk Assessment Agent"
    description = "Analyzes student data to identify at-risk students and suggest interventions"
    default_model = ModelConfig(provider="openai", model_name="gpt-4o", temperature=0.3)
    required_tools = ["student_search", "attendance_analyzer", "grade_lookup"]
    risk_level = "low"  # Can auto-approve risk scores (teacher validates later)
    # ... implementation
```

### 3.3 Agent Registry

```python
# backend/src/infrastructure/ai/agent_registry.py
from __future__ import annotations

from typing import Dict, Optional, Type
from uuid import UUID

from backend.src.domains.ai.agents.base_agent import BaseAgent
from backend.src.domains.ai.agents import (
    AssessmentAgent,
    CommunicationAgent,
    FormsAgent,
    GradebookAgent,
    LessonPlanningAgent,
    ReportAgent,
    StudentRiskAgent,
)
from backend.src.domains.ai.value_objects import AgentKind


class AgentRegistry:
    """Central registry for all AI agents.

    Registered as a singleton in the DI container. Domain services
    resolve agents by kind.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register all built-in agents."""
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
        """Resolve an agent by kind string.

        Raises ``KeyError`` if agent not found.
        """
        if kind not in self._agents:
            raise KeyError(f"Agent not found: {kind}")
        return self._agents[kind]

    def get_or_none(self, kind: str) -> Optional[BaseAgent]:
        return self._agents.get(kind)

    def list_agents(self) -> list[BaseAgent]:
        return list(self._agents.values())

    def register(self, agent: BaseAgent) -> None:
        """Register a custom agent (for plugins or testing)."""
        self._agents[agent.kind.value] = agent
```

### 3.4 DI Container Registration

```python
# backend/src/core/container.py — AI additions
from backend.src.infrastructure.ai.agent_registry import AgentRegistry
from backend.src.infrastructure.ai.providers.openai_provider import OpenAIProvider
from backend.src.infrastructure.ai.providers.base_provider import AIProvider
from backend.src.infrastructure.ai.rag.vector_store import VectorStore
from backend.src.infrastructure.ai.memory.conversation_memory import ConversationMemory

# Register AI services as singletons
container.register(AIProvider, OpenAIProvider, singleton=True)
container.register(AgentRegistry, AgentRegistry, singleton=True)
container.register(VectorStore, VectorStore, singleton=True)
container.register(ConversationMemory, ConversationMemory, singleton=True)
```

---

## 4. Tool Registry Architecture

### 4.1 Tool Interface

```python
# backend/src/domains/ai/tools/base_tool.py
from __future__ import annotations

import abc
from typing import Any, Dict, Optional
from uuid import UUID


class AITool(abc.ABC):
    """Interface for tools that AI agents can invoke.

    Tools are tenant-scoped functions that agents call to interact
    with the TeacherOS platform during execution.
    """

    name: str
    description: str
    # Whether this tool requires tenant context
    requires_tenant: bool = True
    # Whether this tool has side effects (write operations)
    has_side_effects: bool = False

    @abc.abstractmethod
    async def execute(
        self,
        arguments: Dict[str, Any],
        *,
        tenant_id: UUID,
        user_id: UUID,
        run_id: UUID,
    ) -> Dict[str, Any]:
        """Execute the tool with the given arguments.

        Returns a JSON-serializable result dict.
        Raises ``ToolExecutionError`` on failure.
        """
        ...

    @abc.abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return OpenAI-compatible function schema."""
        ...

    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_schema(),
            },
        }
```

### 4.2 Built-in Tools

| Tool Name | Description | Used By | Side Effects |
|---|---|---|---|
| `curriculum_search` | Search MELC database by subject, grade, quarter | LessonPlanning, Assessment | No |
| `melc_lookup` | Get specific MELC details by code | LessonPlanning, Assessment, Report | No |
| `student_search` | Search students by name, LRN, grade level | All agents | No |
| `attendance_analyzer` | Compute attendance statistics for a student/section | StudentRisk, Report | No |
| `grade_lookup` | Retrieve grade data for a student/section/period | Gradebook, StudentRisk | No |
| `rubric_generator` | Generate rubric criteria from learning objectives | Assessment | No |
| `form_template_lookup` | Retrieve DepEd form template structure | Forms | No |
| `transmutation_lookup` | Look up DepEd transmutation table values | Gradebook | No |
| `notification_sender` | Send notifications to teachers/parents | Communication | Yes |
| `student_risk_score` | Write a risk assessment score | StudentRisk | Yes |
| `form_validator` | Validate form data against DepEd rules | Forms | No |
| `school_config_lookup` | Get school configuration and settings | All agents | No |

### 4.3 Tool Registry

```python
# backend/src/infrastructure/ai/tools/tool_registry.py
from __future__ import annotations

from typing import Dict, List, Optional

from backend.src.domains.ai.tools.base_tool import AITool


class ToolRegistry:
    """Central registry for all AI tools.

    Agents reference tools by name. The registry resolves tool instances
    and provides schemas for LLM function calling.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, AITool] = {}

    def register(self, tool: AITool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[AITool]:
        return self._tools.get(name)

    def get_or_raise(self, name: str) -> AITool:
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool not found: {name}")
        return tool

    def get_schemas_for_agent(self, tool_names: List[str]) -> List[Dict]:
        """Return OpenAI tool schemas for the given tool names."""
        schemas = []
        for name in tool_names:
            tool = self._tools.get(name)
            if tool:
                schemas.append(tool.to_openai_tool())
        return schemas

    def list_all(self) -> List[AITool]:
        return list(self._tools.values())
```

### 4.4 Tool Execution Pipeline

```
Agent decides to call tool
        │
        ▼
┌─────────────────────────┐
│  Tool Registry.get()    │──► Tool not found? Return error to agent
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Tenant Scope Check     │──► Tool requires tenant? Verify tenant_id
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Permission Check       │──► RBAC: ai.tool.execute permission
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Input Validation       │──► Validate arguments against schema
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  tool.execute()         │──► Execute with tenant-scoped DB session
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Audit Log              │──► Record tool execution to ai.tool_executions
└────────────┬────────────┘
             │
             ▼
      Return result to agent
```

---

## 5. Prompt Registry Architecture

### 5.1 Prompt Lifecycle

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Create   │────►│  Draft   │────►│  Test    │────►│  Active  │
│  Prompt   │     │  v1      │     │  (A/B)   │     │  (live)  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                      │                  │
                                      │                  ▼
                                      │           ┌──────────┐
                                      └──────────►│ Superseded│
                                                  └──────────┘
```

### 5.2 Prompt Template Engine

```python
# backend/src/infrastructure/ai/prompts/template_engine.py
from __future__ import annotations

from typing import Any, Dict
from jinja2 import Environment, BaseLoader, select_autoescape


class PromptTemplateEngine:
    """Renders prompt templates with variable substitution.

    Uses Jinja2 for template rendering. Templates can include:
    - Variable interpolation: {{ student_name }}
    - Conditionals: {% if grade_level %}...{% endif %}
    - Loops: {% for objective in objectives %}...{% endfor %}
    - Filters: {{ text | truncate(500) }}
    """

    def __init__(self) -> None:
        self._env = Environment(
            loader=BaseLoader(),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template: str, variables: Dict[str, Any]) -> str:
        """Render a template string with the given variables."""
        tpl = self._env.from_string(template)
        return tpl.render(**variables)

    def extract_variables(self, template: str) -> list[str]:
        """Extract variable names used in a template."""
        from jinja2 import meta
        ast = self._env.parse(template)
        return sorted(meta.find_undeclared_variables(ast))
```

### 5.3 Prompt Categories

| Category | Purpose | Example |
|---|---|---|
| **system** | Agent personality, rules, constraints | "You are a DepEd-aligned lesson planning assistant..." |
| **domain** | Domain-specific instructions | "When generating assessment items, always align to MELC..." |
| **few_shot** | Example input/output pairs | Example lesson plan, example quiz item |
| **safety** | Guardrails and content policy | "Never generate content about..." |
| **format** | Output format instructions | "Return JSON with the following schema..." |
| **rag_context** | Retrieved context injection | MELC details, student data, exemplar plans |

### 5.4 Prompt Versioning Strategy

```python
# Each prompt version is immutable once published.
# A/B testing is supported by running the same input against
# multiple prompt versions and comparing output quality.

@dataclass
class PromptABTest:
    """Configuration for prompt A/B testing."""
    prompt_id: UUID
    version_a_id: UUID
    version_b_id: UUID
    traffic_split: float = 0.5  # 50/50
    quality_metric: str = "human_rating"
    min_samples: int = 50
    auto_promote: bool = True  # Auto-promote winner after min_samples
```

---

## 6. Memory Architecture

### 6.1 Memory Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory Architecture                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Working Memory (Redis)                              │    │
│  │  • Per-conversation context window                   │    │
│  │  • TTL: 30 minutes                                   │    │
│  │  • Key: ai:memory:{tenant_id}:{conversation_id}      │    │
│  │  • Stores: last N messages, tool results, context    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Episodic Memory (PostgreSQL)                        │    │
│  │  • ai_conversations + ai_messages tables             │    │
│  │  • Full conversation history per tenant              │    │
│  │  • Queryable, auditable, tenant-scoped               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Semantic Memory (pgvector)                          │    │
│  │  • ai_knowledge_chunks table with embeddings         │    │
│  │  • HNSW index for fast similarity search             │    │
│  │  • Tenant-scoped via RLS                             │    │
│  │  • Content: MELCs, DepEd orders, exemplars           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Procedural Memory (Redis + PostgreSQL)              │    │
│  │  • Cached tool results (attendance stats, grades)    │    │
│  │  • Domain knowledge cache                            │    │
│  │  • TTL: 5 minutes (frequently changing data)         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Working Memory Implementation

```python
# backend/src/infrastructure/ai/memory/working_memory.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis


class WorkingMemory:
    """Redis-backed working memory for AI conversations.

    Stores the recent conversation context that fits within the
    LLM's context window. Automatically evicts old messages when
    the token limit is approached.
    """

    PREFIX = "ai:memory"
    DEFAULT_TTL = 1800  # 30 minutes

    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client

    def _key(self, tenant_id: UUID, conversation_id: UUID) -> str:
        return f"{self.PREFIX}:{tenant_id}:{conversation_id}"

    async def get_context(
        self,
        tenant_id: UUID,
        conversation_id: UUID,
        max_messages: int = 20,
    ) -> List[Dict[str, Any]]:
        """Retrieve the working memory for a conversation."""
        key = self._key(tenant_id, conversation_id)
        raw = await self._redis.lrange(key, -max_messages, -1)
        return [json.loads(msg) for msg in raw]

    async def add_message(
        self,
        tenant_id: UUID,
        conversation_id: UUID,
        message: Dict[str, Any],
        max_size: int = 50,
    ) -> None:
        """Add a message to working memory, trimming if necessary."""
        key = self._key(tenant_id, conversation_id)
        await self._redis.rpush(key, json.dumps(message))
        await self._redis.ltrim(key, -max_size, -1)
        await self._redis.expire(key, self.DEFAULT_TTL)

    async def clear(self, tenant_id: UUID, conversation_id: UUID) -> None:
        """Clear working memory for a conversation."""
        key = self._key(tenant_id, conversation_id)
        await self._redis.delete(key)
```

### 6.3 Conversation Memory (Episodic)

```python
# backend/src/infrastructure/ai/memory/conversation_memory.py
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.infrastructure.ai.db.ai_models import (
    AIConversationModel,
    AIMessageModel,
)


class ConversationMemory:
    """PostgreSQL-backed conversation history.

    Provides durable, auditable, tenant-scoped storage of all
    AI conversations and messages.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_conversation(
        self, conversation_id: UUID, tenant_id: UUID
    ) -> Optional[AIConversationModel]:
        stmt = select(AIConversationModel).where(
            AIConversationModel.id == conversation_id,
            AIConversationModel.tenant_id == tenant_id,
            AIConversationModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_messages(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AIMessageModel]:
        stmt = (
            select(AIMessageModel)
            .where(
                AIMessageModel.conversation_id == conversation_id,
                AIMessageModel.tenant_id == tenant_id,
            )
            .order_by(AIMessageModel.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
```

---

## 7. RAG Architecture

### 7.1 RAG Pipeline Overview

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Document │───►│ Chunk    │───►│ Embed    │───►│ Store    │───►│ Index    │
│ Ingest   │    │ Splitter │    │ Model    │    │ pgvector │    │ HNSW     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘

     ┌──────────────────────────────────────────────────────────────────┐
     │                    Query Time                                    │
     ├──────────────────────────────────────────────────────────────────┤
     │                                                                  │
     │  User Query ──► Embed Query ──► Vector Search ──► Rerank        │
     │                     │                │              │             │
     │                     │           pgvector        Cross-encoder    │
     │                     │           HNSW index      reranker        │
     │                     │           (top-k=20)      (top-k=5)       │
     │                     │                               │            │
     │                     └───────────┬───────────────────┘            │
     │                                 │                                │
     │                          Context Assembly                        │
     │                          (inject into prompt)                    │
     └──────────────────────────────────────────────────────────────────┘
```

### 7.2 Knowledge Sources

| Source | Content | Chunking Strategy | Refresh |
|---|---|---|---|
| **MELCs** | DepEd 2020 Most Essential Learning Competencies | By competency code | On DepEd update |
| **DepEd Orders** | Official memoranda and orders | By section/paragraph | Monthly |
| **SF Templates** | School form structure and rules | By form field group | On template change |
| **Exemplar Plans** | Approved lesson plan examples | By lesson section | On approval |
| **Exemplar Assessments** | Approved assessment items | By question + rationale | On approval |
| **School Policies** | School-specific guidelines | By policy section | On admin update |

### 7.3 Embedding Configuration

```python
# backend/src/infrastructure/ai/rag/embedding_config.py
EMBEDDING_CONFIG = {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "dimensions": 1536,
    "chunk_size": 512,       # tokens per chunk
    "chunk_overlap": 64,     # token overlap between chunks
    "batch_size": 100,       # embeddings per API call
    "max_retrieved_chunks": 10,
    "similarity_threshold": 0.7,
}
```

### 7.4 Vector Store Implementation

```python
# backend/src/infrastructure/ai/rag/vector_store.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.infrastructure.ai.db.ai_models import AIKnowledgeChunkModel


class VectorStore:
    """pgvector-backed vector store for RAG.

    Uses HNSW indexing for fast approximate nearest neighbor search.
    All queries are tenant-scoped via RLS.
    """

    def __init__(self, session: AsyncSession, embedding_fn) -> None:
        self._session = session
        self._embed = embedding_fn  # Callable: str -> List[float]

    async def search(
        self,
        query: str,
        tenant_id: UUID,
        *,
        top_k: int = 10,
        knowledge_types: Optional[List[str]] = None,
        min_score: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Semantic search for relevant knowledge chunks.

        Returns chunks ordered by similarity score (descending).
        """
        query_embedding = await self._embed(query)

        # pgvector cosine similarity search with HNSW index
        sql = text("""
            SELECT id, content, metadata, knowledge_type,
                   1 - (embedding <=> :query_embedding::vector) AS similarity_score
            FROM ai.ai_knowledge_chunks
            WHERE tenant_id = :tenant_id
              AND deleted_at IS NULL
              AND (:knowledge_types IS NULL OR knowledge_type = ANY(:knowledge_types))
              AND 1 - (embedding <=> :query_embedding::vector) > :min_score
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :top_k
        """)

        result = await self._session.execute(sql, {
            "query_embedding": str(query_embedding),
            "tenant_id": tenant_id,
            "knowledge_types": knowledge_types,
            "min_score": min_score,
            "top_k": top_k,
        })

        return [
            {
                "id": row.id,
                "content": row.content,
                "metadata": row.metadata,
                "knowledge_type": row.knowledge_type,
                "score": float(row.similarity_score),
            }
            for row in result.fetchall()
        ]

    async def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        tenant_id: UUID,
    ) -> int:
        """Embed and store knowledge chunks."""
        count = 0
        for chunk in chunks:
            embedding = await self._embed(chunk["content"])
            model = AIKnowledgeChunkModel(
                tenant_id=tenant_id,
                content=chunk["content"],
                embedding=embedding,
                knowledge_type=chunk.get("knowledge_type", "general"),
                source_type=chunk.get("source_type", "manual"),
                source_id=chunk.get("source_id"),
                metadata=chunk.get("metadata", {}),
                chunk_index=chunk.get("chunk_index", 0),
                token_count=chunk.get("token_count", 0),
            )
            self._session.add(model)
            count += 1
        await self._session.flush()
        return count
```

### 7.5 RAG Integration with Agents

```python
# How agents use RAG (in base_agent.py)
async def run_with_rag(self, context: AIInputContext) -> Dict[str, Any]:
    """Execute agent with RAG-enhanced context."""

    # 1. Check if agent needs RAG
    rag_query = await self.get_rag_query(context)
    if rag_query:
        # 2. Retrieve relevant knowledge
        rag_results = await self.vector_store.search(
            query=rag_query,
            tenant_id=context.tenant_id,
            top_k=10,
        )
        context.rag_context = rag_results

    # 3. Build messages (agent injects RAG context into prompt)
    messages = await self.build_messages(context, prompt_version_id)

    # 4. Execute LLM call
    raw_response = await self.llm_provider.chat(messages, self.default_model)

    # 5. Parse and validate
    output = await self.parse_response(raw_response, context)

    # 6. Post-process
    output = await self.post_process(output, context)

    return output
```

---

## 8. AI Workflow Engine

### 8.1 AI Run State Machine

```
                    ┌─────────┐
                    │ QUEUED  │
                    └────┬────┘
                         │ start
                         ▼
                    ┌─────────┐
               ┌───►│ RUNNING │
               │    └────┬────┘
               │         │
               │    ┌────▼────┐
               │    │COMPLETED│──── auto-approve (low risk) ──► DONE
               │    └────┬────┘
               │         │
               │         │ manual review required
               │    ┌────▼────┐
               │    │PENDING  │
               │    │ REVIEW  │
               │    └────┬────┘
               │         │
               │    ┌────▼────┐
               │    │IN_REVIEW│
               │    └────┬────┘
               │         │
               │    ┌────┴────────┐
               │    │             │
               │    ▼             ▼
               │ ┌──────────┐ ┌──────────┐
               │ │ APPROVED │ │ REJECTED │
               │ └──────────┘ └────┬─────┘
               │                   │
               │                   ▼
               │              ┌──────────┐
               │              │ REGENERATE│──► back to RUNNING
               │              └──────────┘
               │
          ┌────┴────┐
          │ FAILED  │──► retry (exponential backoff)
          └─────────┘
               │
               │ max retries exceeded
               ▼
          ┌──────────┐
          │TIMED_OUT │
          └──────────┘
```

### 8.2 Integration with Existing WorkflowEngine

```python
# backend/src/domains/ai/workflow/ai_workflow_config.py
from backend.src.workflow.workflow_engine import WorkflowEngine

# AI run transitions — uses the existing WorkflowEngine
AI_RUN_TRANSITIONS = {
    "queued": {
        "start": "running",
        "cancel": "cancelled",
    },
    "running": {
        "complete": "completed",
        "fail": "failed",
        "timeout": "timed_out",
        "cancel": "cancelled",
    },
    "completed": {
        "approve": "approved",          # auto-approve (low risk)
        "submit_for_review": "pending_review",
        "regenerate": "running",
    },
    "pending_review": {
        "start_review": "in_review",
    },
    "in_review": {
        "approve": "approved",
        "reject": "rejected",
        "edit": "edited",
    },
    "rejected": {
        "regenerate": "running",
        "cancel": "cancelled",
    },
    "failed": {
        "retry": "running",
        "cancel": "cancelled",
    },
    # Terminal states
    "approved": {},
    "edited": {},
    "cancelled": {},
    "timed_out": {"retry": "running"},
}

# Create engine via existing WorkflowEngine class
ai_run_engine = WorkflowEngine(transitions=AI_RUN_TRANSITIONS)
```

### 8.3 Human-in-the-Loop Decision Flow

```python
# backend/src/domains/ai/workflow/review_gate.py

class AIReviewGate:
    """Determines whether an AI output requires human review.

    Risk-based auto-approval policy:
    - LOW risk:    Auto-approve (attendance analysis, data summaries)
    - MEDIUM risk: Require teacher review (lesson plans, assessments)
    - HIGH risk:   Require teacher + principal review (report cards, parent comms)
    """

    AUTO_APPROVE_RISK_LEVELS = {"low"}
    TEACHER_REVIEW_RISK_LEVELS = {"medium"}
    MULTI_REVIEW_RISK_LEVELS = {"high"}

    def should_auto_approve(self, agent_kind: str, output: dict) -> bool:
        agent = self.agent_registry.get(agent_kind)
        return agent.risk_level in self.AUTO_APPROVE_RISK_LEVELS

    def get_reviewers(self, agent_kind: str, tenant_id: UUID) -> list[dict]:
        agent = self.agent_registry.get(agent_kind)
        if agent.risk_level in self.MULTI_REVIEW_RISK_LEVELS:
            return [
                {"role": "teacher", "user_id": output.created_by},
                {"role": "principal", "required": True},
            ]
        elif agent.risk_level in self.TEACHER_REVIEW_RISK_LEVELS:
            return [
                {"role": "teacher", "user_id": output.created_by},
            ]
        return []
```

---

## 9. AI Security Model

### 9.1 Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Security Layers                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Input Validation                                   │
│  ├── Prompt injection detection                              │
│  ├── Input length limits                                     │
│  ├── Content type validation                                 │
│  └── PII detection and redaction                             │
│                                                              │
│  Layer 2: Access Control                                     │
│  ├── RBAC: ai.run, ai.approve, ai.manage_agents             │
│  ├── Tenant isolation via RLS                                │
│  ├── Per-agent permission requirements                       │
│  └── Rate limiting per user/tenant                           │
│                                                              │
│  Layer 3: Data Classification                                │
│  ├── PUBLIC: Reference data (MELCs, templates)               │
│  ├── INTERNAL: Lesson plans, assessment items                │
│  ├── CONFIDENTIAL: Student grades, risk scores               │
│  └── RESTRICTED: PII, disciplinary records                   │
│                                                              │
│  Layer 4: Output Validation                                  │
│  ├── Schema validation (JSON Schema)                         │
│  ├── Content safety filtering                                │
│  ├── PII leakage detection                                   │
│  └── Factual consistency checks                              │
│                                                              │
│  Layer 5: Audit & Compliance                                 │
│  ├── Every AI input/output logged to audit_logs              │
│  ├── Data retention policies                                 │
│  ├── RA 10173 (Data Privacy Act) compliance                  │
│  └── DepEd data handling requirements                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Prompt Injection Guards

```python
# backend/src/infrastructure/ai/security/prompt_guard.py
from __future__ import annotations

import re
from typing import Optional


class PromptInjectionGuard:
    """Detects and prevents prompt injection attacks."""

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"you\s+are\s+now\s+(a|an)\s+",
        r"system\s*:\s*",
        r"<\|system\|>",
        r"\[SYSTEM\]",
        r"override\s+(system|safety)",
        r"jailbreak",
        r"DAN\s+mode",
        r"pretend\s+(you|that)\s+(are|is)",
    ]

    def __init__(self) -> None:
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]

    def detect(self, text: str) -> Optional[str]:
        """Check text for injection patterns.

        Returns the matched pattern description or None if safe.
        """
        for pattern in self._compiled:
            match = pattern.search(text)
            if match:
                return f"Potential injection detected: {match.group()}"
        return None

    def sanitize(self, text: str) -> str:
        """Remove or escape potentially dangerous content."""
        # Strip system-role markers
        text = re.sub(r"<\|.*?\|>", "", text)
        text = re.sub(r"\[SYSTEM\].*?\[/SYSTEM\]", "", text, flags=re.IGNORECASE)
        return text.strip()


class PIIDetector:
    """Detects personally identifiable information in AI inputs/outputs."""

    PII_PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"(\+63|0)9\d{9}",
        "lrn": r"\d{2}-\d{5}-\d{2}-\d{5}",  # DepEd LRN format
        "ssn_ph": r"\d{4}-\d{7}-\d{1}",  # PhilSys/SSS-like
    }

    def detect(self, text: str) -> dict[str, list[str]]:
        """Detect PII in text. Returns dict of type -> matches."""
        findings = {}
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                findings[pii_type] = matches
        return findings

    def redact(self, text: str) -> str:
        """Redact PII from text."""
        for pii_type, pattern in self.PII_PATTERNS.items():
            text = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", text)
        return text
```

### 9.3 AI-Specific RBAC Permissions

```python
# Additional permissions for the AI bounded context
AI_PERMISSIONS = {
    # Agent execution
    "ai.run": ["teacher", "principal", "admin", "deped_staff"],
    "ai.run.risk_assessment": ["principal", "admin", "guidance"],
    "ai.run.report_generation": ["teacher", "principal", "admin"],

    # Output review
    "ai.review": ["teacher", "principal", "admin"],
    "ai.approve": ["teacher", "principal", "admin"],
    "ai.reject": ["teacher", "principal", "admin"],
    "ai.edit_output": ["teacher", "principal", "admin"],

    # Prompt management
    "ai.prompts.read": ["admin", "deped_staff"],
    "ai.prompts.write": ["admin"],
    "ai.prompts.publish": ["admin"],

    # Agent configuration
    "ai.agents.manage": ["admin"],

    # Cost/budget
    "ai.budget.view": ["principal", "admin"],
    "ai.budget.manage": ["admin"],

    # Knowledge base
    "ai.knowledge.read": ["teacher", "principal", "admin"],
    "ai.knowledge.write": ["admin"],
}
```

### 9.4 Rate Limiting

```python
AI_RATE_LIMITS = {
    # Per user
    "user_per_minute": 10,
    "user_per_hour": 100,
    "user_per_day": 500,

    # Per tenant
    "tenant_per_minute": 50,
    "tenant_per_hour": 1000,
    "tenant_per_day": 5000,

    # Per agent kind
    "agent_per_minute": 20,

    # Concurrency
    "tenant_concurrent_runs": 10,
    "user_concurrent_runs": 3,
}
```

---

## 10. Multi-Tenant Isolation Strategy

### 10.1 Tenant Isolation Layers

```
┌─────────────────────────────────────────────────────────────┐
│              Multi-Tenant AI Isolation                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Database Layer (PostgreSQL RLS)                     │    │
│  │  • Every ai.* table has tenant_id + RLS policies     │    │
│  │  • Vector embeddings filtered by tenant_id            │    │
│  │  • Conversation history tenant-scoped                 │    │
│  │  • Prompt registry: shared prompts + tenant overrides │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Cache Layer (Redis)                                  │    │
│  │  • Key prefix: ai:{tenant_id}:*                      │    │
│  │  • Working memory per tenant+conversation             │    │
│  │  • Response cache per tenant                          │    │
│  │  • Rate limit counters per tenant                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Application Layer                                   │    │
│  │  • TenantMiddleware sets app.current_tenant_id        │    │
│  │  • AgentRegistry resolved with tenant context         │    │
│  │  • All AI outputs carry tenant_id                     │    │
│  │  • Celery tasks inherit tenant context                │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Cost Isolation                                      │    │
│  │  • Per-tenant budget limits                           │    │
│  │  • Per-tenant cost tracking                           │    │
│  │  • Per-tenant model restrictions                      │    │
│  │  • Budget alerts per tenant                           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 RLS Policies for AI Tables

```sql
-- All AI tables follow the same RLS pattern

-- ai.agent_runs
ALTER TABLE ai.agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.agent_runs FORCE ROW LEVEL SECURITY;

CREATE POLICY rls_agent_runs_select ON ai.agent_runs
  FOR SELECT USING (tenant_id = core.current_tenant_id());

CREATE POLICY rls_agent_runs_insert ON ai.agent_runs
  FOR INSERT WITH CHECK (tenant_id = core.current_tenant_id());

CREATE POLICY rls_agent_runs_update ON ai.agent_runs
  FOR UPDATE USING (
    tenant_id = core.current_tenant_id()
    AND (created_by = core.current_user_id() OR core.is_tenant_admin())
  );

-- ai.ai_outputs
ALTER TABLE ai.ai_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_outputs FORCE ROW LEVEL SECURITY;

CREATE POLICY rls_ai_outputs_select ON ai.ai_outputs
  FOR SELECT USING (tenant_id = core.current_tenant_id());

CREATE POLICY rls_ai_outputs_insert ON ai.ai_outputs
  FOR INSERT WITH CHECK (tenant_id = core.current_tenant_id());

CREATE POLICY rls_ai_outputs_update ON ai.ai_outputs
  FOR UPDATE USING (
    tenant_id = core.current_tenant_id()
    AND review_state NOT IN ('approved')  -- Cannot modify approved outputs
  );

-- ai.ai_knowledge_chunks (vector store)
ALTER TABLE ai.ai_knowledge_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_knowledge_chunks FORCE ROW LEVEL SECURITY;

CREATE POLICY rls_knowledge_chunks_select ON ai.ai_knowledge_chunks
  FOR SELECT USING (
    tenant_id = core.current_tenant_id()
    OR tenant_id IS NULL  -- Shared reference data visible to all
  );

-- ai.ai_conversations
ALTER TABLE ai.ai_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai.ai_conversations FORCE ROW LEVEL SECURITY;

CREATE POLICY rls_conversations_select ON ai.ai_conversations
  FOR SELECT USING (
    tenant_id = core.current_tenant_id()
    AND (user_id = core.current_user_id() OR core.is_tenant_admin())
  );
```

---

## 11. Cost Tracking System

### 11.1 Cost Tracking Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ AI Run   │───►│ Track    │───►│ Aggregate│───►│ Budget   │
│ Executes │    │ Per-Run  │    │ Daily    │    │ Check    │
│ LLM Call │    │ Cost     │    │ Rollup   │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     │               ▼               ▼               ▼
     │        ai.agent_runs   ai.cost_ledger   ai_budgets
     │        (cost_cents)    (daily totals)   (limits)
     │
     └──► Prometheus: ai_cost_cents_total{tenant, agent, model}
```

### 11.2 Cost Model Pricing (Reference)

| Provider | Model | Input ($/1M tokens) | Output ($/1M tokens) | Cached Input |
|---|---|---|---|---|
| OpenAI | gpt-4o | $2.50 | $10.00 | $1.25 |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 | $0.075 |
| Anthropic | claude-3.5-sonnet | $3.00 | $15.00 | $0.30 |
| Anthropic | claude-3-haiku | $0.25 | $1.25 | $0.03 |

### 11.3 Budget Alert Configuration

```python
# Per-tenant budget configuration
@dataclass
class TenantAIBudget:
    tenant_id: UUID
    monthly_limit_cents: float = 5000.00  # $50/month default
    daily_limit_cents: float = 500.00      # $5/day default
    per_run_limit_cents: float = 100.00    # $1/run default
    alert_threshold_pct: float = 0.80      # 80% warning
    hard_stop_threshold_pct: float = 1.00  # 100% hard stop
    allowed_models: List[str] = field(default_factory=lambda: [
        "gpt-4o", "gpt-4o-mini"
    ])
    max_monthly_runs: int = 1000
```

### 11.4 Cost Dashboard Query

```sql
-- Daily cost summary per tenant
SELECT
    tenant_id,
    DATE(created_at) AS day,
    agent_kind,
    model_used,
    SUM(cost_cents) AS total_cost_cents,
    SUM(prompt_tokens) AS total_prompt_tokens,
    SUM(completion_tokens) AS total_completion_tokens,
    COUNT(*) AS run_count,
    AVG(latency_ms) AS avg_latency_ms
FROM ai.agent_runs
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND status = 'completed'
GROUP BY tenant_id, DATE(created_at), agent_kind, model_used
ORDER BY day DESC, total_cost_cents DESC;
```

---

## 12. Observability Architecture

### 12.1 Metrics

```python
# backend/src/observability/ai_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# --- Run Metrics ---
AI_RUN_DURATION = Histogram(
    "teacheros_ai_run_duration_seconds",
    "AI agent run duration",
    ["agent_kind", "model", "tenant_id"],
    buckets=(1, 2, 5, 10, 30, 60, 120),
)

AI_RUN_TOTAL = Counter(
    "teacheros_ai_run_total",
    "Total AI runs",
    ["agent_kind", "status", "tenant_id"],
)

AI_RUN_ERRORS = Counter(
    "teacheros_ai_run_errors_total",
    "AI run errors",
    ["agent_kind", "error_type", "tenant_id"],
)

# --- Token Metrics ---
AI_TOKENS_TOTAL = Counter(
    "teacheros_ai_tokens_total",
    "Total tokens consumed",
    ["model", "token_type", "tenant_id"],  # token_type: prompt|completion
)

# --- Cost Metrics ---
AI_COST_TOTAL = Counter(
    "teacheros_ai_cost_cents_total",
    "Total AI cost in cents",
    ["agent_kind", "model", "tenant_id"],
)

AI_BUDGET_USAGE = Gauge(
    "teacheros_ai_budget_usage_pct",
    "Budget usage percentage per tenant",
    ["tenant_id", "period"],  # period: monthly|daily
)

# --- Quality Metrics ---
AI_OUTPUT_REVIEW = Counter(
    "teacheros_ai_output_review_total",
    "AI output review outcomes",
    ["agent_kind", "review_state", "tenant_id"],
)

AI_FEEDBACK_RATING = Histogram(
    "teacheros_ai_feedback_rating",
    "AI output feedback ratings",
    ["agent_kind"],
    buckets=(1, 2, 3, 4, 5),
)

# --- RAG Metrics ---
AI_RAG_SEARCH_DURATION = Histogram(
    "teacheros_ai_rag_search_duration_seconds",
    "RAG vector search duration",
    ["tenant_id"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
)

AI_RAG_CHUNKS_RETRIEVED = Histogram(
    "teacheros_ai_rag_chunks_retrieved",
    "Number of RAG chunks retrieved per query",
    ["tenant_id"],
    buckets=(0, 1, 3, 5, 10, 20),
)

# --- Tool Metrics ---
AI_TOOL_EXECUTION = Counter(
    "teacheros_ai_tool_execution_total",
    "Tool executions by agents",
    ["tool_name", "success", "agent_kind"],
)

AI_TOOL_DURATION = Histogram(
    "teacheros_ai_tool_duration_seconds",
    "Tool execution duration",
    ["tool_name"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)
```

### 12.2 Distributed Tracing

```python
# backend/src/infrastructure/ai/tracing.py
from opentelemetry import trace

tracer = trace.get_tracer("teacheros.ai")


async def trace_agent_run(agent_kind: str, tenant_id: str):
    """Create a distributed trace span for an AI agent run."""
    with tracer.start_as_current_span(
        f"ai.agent.{agent_kind}",
        attributes={
            "ai.agent.kind": agent_kind,
            "tenant.id": tenant_id,
        },
    ) as span:
        yield span


async def trace_llm_call(provider: str, model: str):
    """Trace an individual LLM API call."""
    with tracer.start_as_current_span(
        f"ai.llm.{provider}.{model}",
        attributes={
            "ai.provider": provider,
            "ai.model": model,
        },
    ) as span:
        yield span


async def trace_rag_search(top_k: int):
    """Trace a RAG retrieval."""
    with tracer.start_as_current_span(
        "ai.rag.search",
        attributes={"ai.rag.top_k": top_k},
    ) as span:
        yield span
```

### 12.3 Structured Logging

```python
# AI runs produce structured JSON logs
AI_RUN_LOG_TEMPLATE = {
    "event": "ai_run_completed",
    "run_id": "{run_id}",
    "agent_kind": "{agent_kind}",
    "tenant_id": "{tenant_id}",
    "user_id": "{user_id}",
    "model": "{model}",
    "provider": "{provider}",
    "prompt_tokens": "{prompt_tokens}",
    "completion_tokens": "{completion_tokens}",
    "total_tokens": "{total_tokens}",
    "cost_cents": "{cost_cents}",
    "latency_ms": "{latency_ms}",
    "status": "{status}",
    "review_state": "{review_state}",
    "request_id": "{request_id}",
}
```

---

## 13. Event Architecture

### 13.1 AI Domain Events

All AI events are published to the existing `audit.domain_events` table via PostgreSQL triggers, consistent with the TeacherOS event-driven architecture.

```sql
-- AI events emitted via triggers on ai.agent_runs and ai.ai_outputs

-- Trigger on agent_runs for run lifecycle events
CREATE OR REPLACE FUNCTION ai.tg_emit_agent_run_event() RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO audit.domain_events
      (tenant_id, event_type, aggregate_type, aggregate_id, payload, produced_by)
    VALUES
      (NEW.tenant_id, 'ai.run.started', 'agent_run', NEW.id,
       jsonb_build_object(
         'run_id', NEW.id,
         'agent_kind', NEW.agent_kind,
         'model', NEW.model_used,
         'user_id', NEW.created_by
       ),
       NEW.created_by);
  ELSIF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
    INSERT INTO audit.domain_events
      (tenant_id, event_type, aggregate_type, aggregate_id, payload, produced_by)
    VALUES
      (NEW.tenant_id,
       CASE NEW.status
         WHEN 'completed' THEN 'ai.run.completed'
         WHEN 'failed' THEN 'ai.run.failed'
         WHEN 'cancelled' THEN 'ai.run.cancelled'
         ELSE 'ai.run.status_changed'
       END,
       'agent_run', NEW.id,
       jsonb_build_object(
         'run_id', NEW.id,
         'agent_kind', NEW.agent_kind,
         'old_status', OLD.status,
         'new_status', NEW.status,
         'cost_cents', NEW.cost_cents,
         'latency_ms', NEW.latency_ms
       ),
       NEW.updated_by);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_emit_agent_run_events
  AFTER INSERT OR UPDATE ON ai.agent_runs
  FOR EACH ROW EXECUTE FUNCTION ai.tg_emit_agent_run_event();
```

### 13.2 Event Consumption

```python
# backend/src/events/handlers/ai_event_handlers.py

class AIOutputApprovedHandler:
    """Handle AI output approval — apply to domain context."""

    async def handle(self, event: AIOutputReviewed):
        if event.review_state != "approved":
            return

        output = await self.output_repo.get(event.output_id)

        # Route to appropriate domain service based on domain_type
        match output.domain_type:
            case "lesson_plan":
                await self.lesson_service.apply_ai_output(
                    output.domain_id, output.payload
                )
            case "assessment":
                await self.assessment_service.create_from_ai_output(
                    output.domain_id, output.payload
                )
            case "risk_assessment":
                await self.risk_service.record_assessment(
                    output.domain_id, output.payload
                )
            case "school_form":
                await self.form_service.populate_from_ai_output(
                    output.domain_id, output.payload
                )
            case "report":
                await self.report_service.apply_ai_output(
                    output.domain_id, output.payload
                )
            case "communication":
                await self.comms_service.send_from_ai_output(
                    output.domain_id, output.payload
                )

        # Audit log
        await self.audit_service.log(
            event_kind="ai.output_approved",
            target_type=output.domain_type,
            target_id=output.domain_id,
            tenant_id=event.tenant_id,
        )
```

### 13.3 Event Routing Table

| Event Type | Producer | Consumer(s) | Action |
|---|---|---|---|
| `ai.run.started` | AgentRunner | AuditLogger | Log run start |
| `ai.run.completed` | AgentRunner | AuditLogger, MetricsCollector | Log completion, update metrics |
| `ai.run.failed` | AgentRunner | AuditLogger, NotificationService | Log failure, notify user |
| `ai.output.generated` | AgentRunner | AuditLogger | Log output creation |
| `ai.output.approved` | ReviewGate | DomainService (per domain_type), AuditLogger | Apply output to domain |
| `ai.output.rejected` | ReviewGate | AuditLogger, NotificationService | Log rejection, notify user |
| `ai.feedback.submitted` | ReviewService | AuditLogger, MetricsCollector | Log feedback, update quality scores |
| `ai.budget.alert` | BudgetService | NotificationService, AuditLogger | Alert admins |

---

## 14. Database Schema

### 14.1 Complete AI Schema DDL

```sql
-- =============================================================
-- Module 12: AI Agents & Intelligence Platform
-- Depends on: 01-auth-organization.sql
-- Tables: ai_agents, agent_runs, ai_outputs, ai_output_versions,
--         prompts, prompt_versions, ai_conversations, ai_messages,
--         ai_feedback, ai_knowledge_chunks, ai_tool_executions,
--         ai_budgets, ai_cost_ledger
-- =============================================================

CREATE SCHEMA IF NOT EXISTS ai;
SET search_path TO ai, core, public;

-- =============================================================
-- ENUMS
-- =============================================================
CREATE TYPE agent_kind AS ENUM (
  'lesson_planning', 'assessment', 'gradebook', 'forms',
  'student_risk', 'report', 'communication',
  -- Post-MVP
  'rubric_generation', 'curriculum_alignment',
  'attendance_analysis', 'parent_summary', 'compliance_check'
);

CREATE TYPE agent_status AS ENUM ('active', 'inactive', 'deprecated');

CREATE TYPE run_status AS ENUM (
  'queued', 'running', 'completed', 'failed', 'cancelled', 'timed_out'
);

CREATE TYPE review_state AS ENUM (
  'pending', 'in_review', 'approved', 'rejected', 'edited', 'auto_approved'
);

CREATE TYPE output_supersession_reason AS ENUM (
  'regenerated', 'edited', 'prompt_updated', 'correction'
);

CREATE TYPE conversation_status AS ENUM ('active', 'archived', 'deleted');

CREATE TYPE message_role AS ENUM ('system', 'user', 'assistant', 'tool');

CREATE TYPE prompt_category AS ENUM (
  'system', 'domain', 'few_shot', 'safety', 'format', 'rag_context'
);

CREATE TYPE knowledge_type AS ENUM (
  'melc', 'deped_order', 'sf_template', 'exemplar_lesson',
  'exemplar_assessment', 'school_policy', 'general'
);

CREATE TYPE feedback_type AS ENUM ('rating', 'correction', 'suggestion', 'bug_report');

-- =============================================================
-- 1. ai_agents — Agent registry
-- =============================================================
CREATE TABLE ai_agents (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,                        -- NULL = platform-wide agent
  name                  TEXT NOT NULL,
  kind                  agent_kind NOT NULL UNIQUE,
  description           TEXT,
  default_model         JSONB NOT NULL DEFAULT '{}'::jsonb,
  -- e.g., {"provider": "openai", "model": "gpt-4o", "temperature": 0.7}
  available_models      JSONB NOT NULL DEFAULT '[]'::jsonb,
  required_tools        TEXT[] NOT NULL DEFAULT '{}',
  optional_tools        TEXT[] NOT NULL DEFAULT '{}',
  risk_level            TEXT NOT NULL DEFAULT 'medium'
                        CHECK (risk_level IN ('low', 'medium', 'high')),
  supports_streaming    BOOLEAN NOT NULL DEFAULT TRUE,
  supports_conversation BOOLEAN NOT NULL DEFAULT FALSE,
  config                JSONB NOT NULL DEFAULT '{}'::jsonb,
  status                agent_status NOT NULL DEFAULT 'active',
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID REFERENCES core.users(id),
  updated_by            UUID REFERENCES core.users(id),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_aa_kind ON ai_agents(kind) WHERE deleted_at IS NULL;
CREATE INDEX idx_aa_status ON ai_agents(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_aa_tenant ON ai_agents(tenant_id) WHERE tenant_id IS NOT NULL AND deleted_at IS NULL;

COMMENT ON TABLE ai_agents IS 'Registry of all AI agent types available in the platform.';

-- =============================================================
-- 2. agent_runs — Execution history with cost tracking
-- =============================================================
CREATE TABLE agent_runs (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  agent_kind            agent_kind NOT NULL,
  agent_id              UUID NOT NULL REFERENCES ai_agents(id) ON DELETE RESTRICT,
  prompt_id             UUID,                        -- which prompt version was used
  prompt_version_id     UUID,
  user_id               UUID NOT NULL REFERENCES core.users(id),
  -- Input
  input_context         JSONB NOT NULL DEFAULT '{}'::jsonb,
  input_hash            TEXT,                        -- SHA-256 for dedup
  -- Output
  status                run_status NOT NULL DEFAULT 'queued',
  output_id             UUID,                        -- FK to ai_outputs after completion
  raw_response          TEXT,                        -- raw LLM response
  parsed_output         JSONB,                       -- structured output
  -- Model info
  model_used            TEXT NOT NULL,
  provider              TEXT NOT NULL,
  -- Token tracking
  prompt_tokens         INT NOT NULL DEFAULT 0,
  completion_tokens     INT NOT NULL DEFAULT 0,
  total_tokens          INT NOT NULL DEFAULT 0,
  cached_tokens         INT NOT NULL DEFAULT 0,
  -- Cost tracking
  cost_cents            NUMERIC(10,4) NOT NULL DEFAULT 0,
  -- Performance
  latency_ms            INT,                         -- total run latency
  llm_latency_ms        INT,                         -- just the LLM call
  -- Error handling
  error_type            TEXT,
  error_message         TEXT,
  retry_count           INT NOT NULL DEFAULT 0,
  max_retries           INT NOT NULL DEFAULT 3,
  -- Context
  conversation_id       UUID,                        -- if part of a conversation
  correlation_id        UUID,                        -- for tracing
  request_id            TEXT,                        -- API request ID
  -- Timestamps
  started_at            TIMESTAMPTZ,
  completed_at          TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_ar_tenant ON agent_runs(tenant_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_ar_agent ON agent_runs(agent_kind, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_ar_user ON agent_runs(user_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_ar_status ON agent_runs(status) WHERE status IN ('queued', 'running') AND deleted_at IS NULL;
CREATE INDEX idx_ar_conversation ON agent_runs(conversation_id) WHERE conversation_id IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX idx_ar_cost ON agent_runs(tenant_id, cost_cents) WHERE deleted_at IS NULL;
CREATE INDEX idx_ar_created_brin ON agent_runs USING brin (created_at);

COMMENT ON TABLE agent_runs IS 'Immutable execution history for every AI agent run. Includes token and cost tracking.';

-- =============================================================
-- 3. ai_outputs — Immutable output store with provenance
-- =============================================================
CREATE TABLE ai_outputs (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  run_id                UUID NOT NULL REFERENCES agent_runs(id) ON DELETE RESTRICT,
  agent_kind            agent_kind NOT NULL,
  -- Output content
  payload               JSONB NOT NULL,              -- the structured AI output
  output_version        INT NOT NULL DEFAULT 1,
  supersedes_id         UUID REFERENCES ai_outputs(id) ON DELETE SET NULL,
  supersession_reason   output_supersession_reason,
  -- Human review
  review_state          review_state NOT NULL DEFAULT 'pending',
  reviewed_by           UUID REFERENCES core.users(id),
  reviewed_at           TIMESTAMPTZ,
  review_notes          TEXT,
  -- Domain linkage (which domain object this output is for)
  domain_type           TEXT,                        -- 'lesson_plan', 'assessment', etc.
  domain_id             UUID,                        -- FK to the domain object
  -- Provenance
  model_used            TEXT NOT NULL,
  provider              TEXT NOT NULL,
  prompt_version_id     UUID,
  system_prompt_hash    TEXT,                        -- SHA-256
  input_hash            TEXT,
  -- Cost (denormalized from run for fast queries)
  cost_cents            NUMERIC(10,4) NOT NULL DEFAULT 0,
  token_usage           JSONB NOT NULL DEFAULT '{}'::jsonb,
  -- Timestamps
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID REFERENCES core.users(id),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_ao_tenant ON ai_outputs(tenant_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_ao_run ON ai_outputs(run_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ao_domain ON ai_outputs(domain_type, domain_id) WHERE domain_id IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX idx_ao_review ON ai_outputs(review_state) WHERE review_state IN ('pending', 'in_review') AND deleted_at IS NULL;
CREATE INDEX idx_ao_agent ON ai_outputs(agent_kind, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_ao_supersedes ON ai_outputs(supersedes_id) WHERE supersedes_id IS NOT NULL AND deleted_at IS NULL;

COMMENT ON TABLE ai_outputs IS 'Immutable store of all AI-generated outputs. Approved outputs are never modified; new versions supersede old ones.';

-- =============================================================
-- 4. prompts — Prompt registry
-- =============================================================
CREATE TABLE prompts (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,                        -- NULL = platform prompt
  name                  TEXT NOT NULL,
  description           TEXT,
  category              prompt_category NOT NULL,
  agent_kind            agent_kind,                  -- NULL = cross-agent prompt
  current_version_id    UUID,
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID REFERENCES core.users(id),
  updated_by            UUID REFERENCES core.users(id),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_prompts_agent ON prompts(agent_kind) WHERE agent_kind IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX idx_prompts_category ON prompts(category) WHERE deleted_at IS NULL;
CREATE INDEX idx_prompts_tenant ON prompts(tenant_id) WHERE tenant_id IS NOT NULL AND deleted_at IS NULL;

COMMENT ON TABLE prompts IS 'Registry of all prompt templates. Each prompt can have multiple versions.';

-- =============================================================
-- 5. prompt_versions — Versioned prompt templates
-- =============================================================
CREATE TABLE prompt_versions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prompt_id             UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
  version_number        INT NOT NULL,
  -- Template content
  system_prompt         TEXT NOT NULL,
  user_template         TEXT NOT NULL,                -- Jinja2 template
  few_shot_examples     JSONB NOT NULL DEFAULT '[]'::jsonb,
  safety_prompt         TEXT,
  format_instructions   TEXT,
  -- Variables this template expects
  variables             TEXT[] NOT NULL DEFAULT '{}',
  -- Validation
  output_schema         JSONB,                       -- JSON Schema for validation
  -- Status
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  -- A/B testing
  ab_test_group         TEXT,                        -- 'control', 'variant_a', 'variant_b'
  -- Metadata
  token_estimate        INT,                         -- estimated token count
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID REFERENCES core.users(id),
  UNIQUE (prompt_id, version_number)
);

CREATE INDEX idx_pv_prompt ON prompt_versions(prompt_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_pv_active ON prompt_versions(prompt_id, is_active) WHERE is_active = TRUE;

COMMENT ON TABLE prompt_versions IS 'Immutable versions of prompt templates. New versions supersede old ones.';

-- =============================================================
-- 6. ai_conversations — Multi-turn conversation sessions
-- =============================================================
CREATE TABLE ai_conversations (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  agent_kind            agent_kind NOT NULL,
  user_id               UUID NOT NULL REFERENCES core.users(id),
  title                 TEXT,
  status                conversation_status NOT NULL DEFAULT 'active',
  message_count         INT NOT NULL DEFAULT 0,
  total_tokens          INT NOT NULL DEFAULT 0,
  total_cost_cents      NUMERIC(10,4) NOT NULL DEFAULT 0,
  -- Domain context
  domain_type           TEXT,                        -- which domain object this conversation is about
  domain_id             UUID,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_ac_tenant_user ON ai_conversations(tenant_id, user_id, updated_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_ac_agent ON ai_conversations(agent_kind, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_ac_domain ON ai_conversations(domain_type, domain_id) WHERE domain_id IS NOT NULL AND deleted_at IS NULL;

-- =============================================================
-- 7. ai_messages — Individual messages in conversations
-- =============================================================
CREATE TABLE ai_messages (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id       UUID NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  role                  message_role NOT NULL,
  content               TEXT NOT NULL,
  -- Tool use
  tool_calls            JSONB DEFAULT '[]'::jsonb,
  tool_call_id          TEXT,
  -- Token tracking
  prompt_tokens         INT NOT NULL DEFAULT 0,
  completion_tokens     INT NOT NULL DEFAULT 0,
  model_used            TEXT,
  cost_cents            NUMERIC(10,4) NOT NULL DEFAULT 0,
  -- Metadata
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_am_conversation ON ai_messages(conversation_id, created_at ASC);
CREATE INDEX idx_am_tenant ON ai_messages(tenant_id, created_at DESC);

-- =============================================================
-- 8. ai_feedback — Human feedback on AI outputs
-- =============================================================
CREATE TABLE ai_feedback (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  output_id             UUID NOT NULL REFERENCES ai_outputs(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  reviewer_id           UUID NOT NULL REFERENCES core.users(id),
  feedback_type         feedback_type NOT NULL,
  rating                INT CHECK (rating BETWEEN 1 AND 5),
  comment               TEXT,
  edited_output         JSONB,                       -- if user edited and resubmitted
  -- Classification
  quality_tags          TEXT[] DEFAULT '{}',          -- 'accurate', 'helpful', 'inaccurate', etc.
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_af_output ON ai_feedback(output_id);
CREATE INDEX idx_af_tenant ON ai_feedback(tenant_id, created_at DESC);
CREATE INDEX idx_af_reviewer ON ai_feedback(reviewer_id, created_at DESC);

COMMENT ON TABLE ai_feedback IS 'Human feedback on AI outputs. Used for quality tracking and prompt improvement.';

-- =============================================================
-- 9. ai_knowledge_chunks — RAG document chunks with embeddings
-- =============================================================
CREATE TABLE ai_knowledge_chunks (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,                        -- NULL = shared reference data
  -- Content
  content               TEXT NOT NULL,
  embedding             vector(1536),                -- pgvector embedding
  -- Source
  knowledge_type        knowledge_type NOT NULL,
  source_type           TEXT NOT NULL,               -- 'melc', 'deped_order', 'lesson_plan', etc.
  source_id             UUID,                        -- FK to source document
  chunk_index           INT NOT NULL DEFAULT 0,
  token_count           INT NOT NULL DEFAULT 0,
  -- Metadata
  title                 TEXT,
  tags                  TEXT[] DEFAULT '{}',
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- HNSW index for fast approximate nearest neighbor search
CREATE INDEX idx_akc_embedding ON ai_knowledge_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_akc_tenant_type ON ai_knowledge_chunks(tenant_id, knowledge_type)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_akc_source ON ai_knowledge_chunks(source_type, source_id)
  WHERE source_id IS NOT NULL AND deleted_at IS NULL;

COMMENT ON TABLE ai_knowledge_chunks IS 'Document chunks with vector embeddings for RAG retrieval. Tenant-scoped via RLS.';

-- =============================================================
-- 10. ai_tool_executions — Tool usage audit log
-- =============================================================
CREATE TABLE ai_tool_executions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id                UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  tool_name             TEXT NOT NULL,
  arguments             JSONB NOT NULL DEFAULT '{}'::jsonb,
  result                JSONB,
  success               BOOLEAN NOT NULL DEFAULT TRUE,
  error_message         TEXT,
  latency_ms            INT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ate_run ON ai_tool_executions(run_id);
CREATE INDEX idx_ate_tenant ON ai_tool_executions(tenant_id, created_at DESC);
CREATE INDEX idx_ate_tool ON ai_tool_executions(tool_name, created_at DESC);

-- =============================================================
-- 11. ai_budgets — Per-tenant budget configuration
-- =============================================================
CREATE TABLE ai_budgets (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL UNIQUE,
  monthly_limit_cents   NUMERIC(10,2) NOT NULL DEFAULT 5000.00,
  daily_limit_cents     NUMERIC(10,2) NOT NULL DEFAULT 500.00,
  per_run_limit_cents   NUMERIC(10,2) NOT NULL DEFAULT 100.00,
  alert_threshold_pct   NUMERIC(5,2) NOT NULL DEFAULT 80.00,
  hard_stop_enabled     BOOLEAN NOT NULL DEFAULT TRUE,
  allowed_models        TEXT[] NOT NULL DEFAULT '{gpt-4o,gpt-4o-mini}',
  max_monthly_runs      INT NOT NULL DEFAULT 1000,
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID REFERENCES core.users(id)
);

-- =============================================================
-- 12. ai_cost_ledger — Aggregated cost tracking
-- =============================================================
CREATE TABLE ai_cost_ledger (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  period_date           DATE NOT NULL,
  agent_kind            agent_kind,
  model_used            TEXT,
  -- Aggregated metrics
  total_runs            INT NOT NULL DEFAULT 0,
  total_prompt_tokens   BIGINT NOT NULL DEFAULT 0,
  total_completion_tokens BIGINT NOT NULL DEFAULT 0,
  total_cost_cents      NUMERIC(10,4) NOT NULL DEFAULT 0,
  avg_latency_ms        NUMERIC(10,2),
  -- Budget tracking
  budget_remaining_cents NUMERIC(10,2),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, period_date, agent_kind, model_used)
);

CREATE INDEX idx_acl_tenant_date ON ai_cost_ledger(tenant_id, period_date DESC);
CREATE INDEX idx_acl_budget ON ai_cost_ledger(tenant_id, period_date DESC, budget_remaining_cents);

-- =============================================================
-- 13. Triggers
-- =============================================================
DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'ai_agents', 'agent_runs', 'ai_outputs', 'prompts',
    'ai_conversations', 'ai_knowledge_chunks', 'ai_budgets', 'ai_cost_ledger'
  ])
  LOOP
    EXECUTE format('
      CREATE TRIGGER tg_set_updated_at BEFORE UPDATE ON ai.%I
        FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
    ', t);
  END LOOP;
END $$;

-- Agent run status change trigger (emits domain events)
CREATE TRIGGER tg_emit_agent_run_events
  AFTER INSERT OR UPDATE ON ai.agent_runs
  FOR EACH ROW EXECUTE FUNCTION ai.tg_emit_agent_run_event();

-- =============================================================
-- 14. RLS Policies
-- =============================================================
ALTER TABLE ai_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_agents FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_aa_read ON ai_agents
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR tenant_id IS NULL OR core.is_system_admin());
CREATE POLICY rls_aa_write ON ai_agents
  FOR ALL USING (core.is_system_admin() OR core.is_tenant_admin());

ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ar_read ON agent_runs
  FOR SELECT USING (tenant_id = core.current_tenant_id());
CREATE POLICY rls_ar_insert ON agent_runs
  FOR INSERT WITH CHECK (tenant_id = core.current_tenant_id());
CREATE POLICY rls_ar_update ON agent_runs
  FOR UPDATE USING (tenant_id = core.current_tenant_id());

ALTER TABLE ai_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_outputs FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ao_read ON ai_outputs
  FOR SELECT USING (tenant_id = core.current_tenant_id());
CREATE POLICY rls_ao_insert ON ai_outputs
  FOR INSERT WITH CHECK (tenant_id = core.current_tenant_id());
CREATE POLICY rls_ao_update ON ai_outputs
  FOR UPDATE USING (tenant_id = core.current_tenant_id());

ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompts FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_prompts_read ON prompts
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR tenant_id IS NULL);

ALTER TABLE prompt_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_pv_read ON prompt_versions
  FOR SELECT USING (TRUE);  -- versions readable by all authenticated users

ALTER TABLE ai_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_conversations FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ac_read ON ai_conversations
  FOR SELECT USING (
    tenant_id = core.current_tenant_id()
    AND (user_id = core.current_user_id() OR core.is_tenant_admin())
  );
CREATE POLICY rls_ac_insert ON ai_conversations
  FOR INSERT WITH CHECK (tenant_id = core.current_tenant_id());

ALTER TABLE ai_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_messages FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_am_read ON ai_messages
  FOR SELECT USING (tenant_id = core.current_tenant_id());
CREATE POLICY rls_am_insert ON ai_messages
  FOR INSERT WITH CHECK (tenant_id = core.current_tenant_id());

ALTER TABLE ai_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_feedback FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_af_read ON ai_feedback
  FOR SELECT USING (tenant_id = core.current_tenant_id());
CREATE POLICY rls_af_insert ON ai_feedback
  FOR INSERT WITH CHECK (tenant_id = core.current_tenant_id());

ALTER TABLE ai_knowledge_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_knowledge_chunks FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_akc_read ON ai_knowledge_chunks
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR tenant_id IS NULL);
CREATE POLICY rls_akc_insert ON ai_knowledge_chunks
  FOR INSERT WITH CHECK (tenant_id = core.current_tenant_id() OR core.is_system_admin());

ALTER TABLE ai_tool_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_tool_executions FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ate_read ON ai_tool_executions
  FOR SELECT USING (tenant_id = core.current_tenant_id());

ALTER TABLE ai_budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_budgets FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ab_read ON ai_budgets
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ab_write ON ai_budgets
  FOR ALL USING (core.is_system_admin());

ALTER TABLE ai_cost_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_cost_ledger FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_acl_read ON ai_cost_ledger
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());

-- =============================================================
-- End of Module 12
-- =============================================================
```

---

## 15. API Contracts

### 15.1 REST Endpoints

| Method | Path | Description | Permission | Response |
|---|---|---|---|---|
| `GET` | `/api/v1/ai/agents` | List available agents | `ai.run` | `AgentListResponse` |
| `GET` | `/api/v1/ai/agents/{kind}` | Get agent details | `ai.run` | `AgentDetailResponse` |
| `POST` | `/api/v1/ai/agents/{kind}/run` | Execute an agent | `ai.run` | `AgentRunResponse` |
| `POST` | `/api/v1/ai/agents/{kind}/run/stream` | Execute with streaming | `ai.run` | SSE stream |
| `GET` | `/api/v1/ai/runs` | List AI runs | `ai.run` | `RunListResponse` |
| `GET` | `/api/v1/ai/runs/{run_id}` | Get run details | `ai.run` | `RunDetailResponse` |
| `POST` | `/api/v1/ai/runs/{run_id}/cancel` | Cancel a running task | `ai.run` | `RunDetailResponse` |
| `GET` | `/api/v1/ai/outputs` | List AI outputs | `ai.review` | `OutputListResponse` |
| `GET` | `/api/v1/ai/outputs/{output_id}` | Get output details | `ai.review` | `OutputDetailResponse` |
| `POST` | `/api/v1/ai/outputs/{output_id}/approve` | Approve output | `ai.approve` | `OutputDetailResponse` |
| `POST` | `/api/v1/ai/outputs/{output_id}/reject` | Reject output | `ai.reject` | `OutputDetailResponse` |
| `POST` | `/api/v1/ai/outputs/{output_id}/edit` | Edit and resubmit | `ai.edit_output` | `OutputDetailResponse` |
| `POST` | `/api/v1/ai/outputs/{output_id}/regenerate` | Regenerate output | `ai.run` | `AgentRunResponse` |
| `POST` | `/api/v1/ai/outputs/{output_id}/feedback` | Submit feedback | `ai.review` | `FeedbackResponse` |
| `GET` | `/api/v1/ai/prompts` | List prompts | `ai.prompts.read` | `PromptListResponse` |
| `POST` | `/api/v1/ai/prompts` | Create prompt | `ai.prompts.write` | `PromptResponse` |
| `GET` | `/api/v1/ai/prompts/{prompt_id}` | Get prompt with versions | `ai.prompts.read` | `PromptDetailResponse` |
| `POST` | `/api/v1/ai/prompts/{prompt_id}/versions` | Create version | `ai.prompts.write` | `PromptVersionResponse` |
| `POST` | `/api/v1/ai/prompts/{prompt_id}/versions/{version_id}/activate` | Activate version | `ai.prompts.publish` | `PromptVersionResponse` |
| `GET` | `/api/v1/ai/conversations` | List conversations | `ai.run` | `ConversationListResponse` |
| `POST` | `/api/v1/ai/conversations` | Start conversation | `ai.run` | `ConversationResponse` |
| `GET` | `/api/v1/ai/conversations/{conv_id}` | Get conversation | `ai.run` | `ConversationDetailResponse` |
| `POST` | `/api/v1/ai/conversations/{conv_id}/messages` | Send message | `ai.run` | `MessageResponse` |
| `GET` | `/api/v1/ai/costs` | Cost dashboard | `ai.budget.view` | `CostDashboardResponse` |
| `GET` | `/api/v1/ai/costs/breakdown` | Detailed cost breakdown | `ai.budget.view` | `CostBreakdownResponse` |
| `GET` | `/api/v1/ai/budget` | Get budget config | `ai.budget.view` | `BudgetResponse` |
| `PUT` | `/api/v1/ai/budget` | Update budget | `ai.budget.manage` | `BudgetResponse` |
| `GET` | `/api/v1/ai/feedback` | Feedback summary | `ai.review` | `FeedbackSummaryResponse` |
| `GET` | `/api/v1/ai/knowledge` | List knowledge chunks | `ai.knowledge.read` | `KnowledgeListResponse` |
| `POST` | `/api/v1/ai/knowledge` | Ingest knowledge | `ai.knowledge.write` | `KnowledgeIngestResponse` |

### 15.2 Key Request/Response Schemas

```python
# backend/src/schemas/ai.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Agent Schemas ---
class AgentListResponse(BaseModel):
    agents: List[AgentSummary]
    total: int


class AgentSummary(BaseModel):
    kind: str
    name: str
    description: str
    risk_level: str
    supports_streaming: bool
    supports_conversation: bool
    available_models: List[str]


class AgentRunRequest(BaseModel):
    """Request to execute an AI agent."""
    domain_data: Dict[str, Any] = Field(..., description="Domain-specific input payload")
    conversation_id: Optional[UUID] = Field(None, description="Existing conversation to continue")
    model_override: Optional[str] = Field(None, description="Override the default model")
    temperature_override: Optional[float] = Field(None, ge=0, le=2)
    max_tokens_override: Optional[int] = Field(None, ge=1, le=16384)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class AgentRunResponse(BaseModel):
    """Response from an AI agent run (async)."""
    run_id: UUID
    status: str  # "queued" | "completed" (sync) | "running" (streaming)
    agent_kind: str
    output_id: Optional[UUID] = None
    review_state: Optional[str] = None
    cost_cents: Optional[float] = None
    latency_ms: Optional[int] = None


# --- Output Schemas ---
class OutputDetailResponse(BaseModel):
    id: UUID
    run_id: UUID
    agent_kind: str
    payload: Dict[str, Any]
    review_state: str
    output_version: int
    model_used: str
    cost_cents: float
    token_usage: Dict[str, int]
    domain_type: Optional[str] = None
    domain_id: Optional[UUID] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class OutputReviewRequest(BaseModel):
    review_state: str = Field(..., pattern="^(approved|rejected)$")
    notes: Optional[str] = None


class OutputEditRequest(BaseModel):
    edited_payload: Dict[str, Any] = Field(..., description="The edited output content")
    notes: Optional[str] = None


# --- Conversation Schemas ---
class ConversationResponse(BaseModel):
    id: UUID
    agent_kind: str
    title: Optional[str]
    status: str
    message_count: int
    total_cost_cents: float
    created_at: datetime
    updated_at: datetime


class MessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    tool_calls: List[Dict[str, Any]]
    token_usage: Optional[Dict[str, int]]
    cost_cents: float
    created_at: datetime


# --- Cost Schemas ---
class CostDashboardResponse(BaseModel):
    tenant_id: UUID
    period: str  # "monthly" | "daily"
    total_cost_cents: float
    budget_limit_cents: float
    budget_remaining_cents: float
    budget_usage_pct: float
    total_runs: int
    total_tokens: int
    by_agent: List[CostByAgent]
    by_model: List[CostByModel]
    daily_trend: List[CostDailyPoint]


class CostByAgent(BaseModel):
    agent_kind: str
    total_cost_cents: float
    run_count: int
    avg_cost_per_run: float


class CostByModel(BaseModel):
    model: str
    provider: str
    total_cost_cents: float
    run_count: int


class CostDailyPoint(BaseModel):
    date: str
    cost_cents: float
    runs: int
    tokens: int
```

---

## 16. WebSocket Contracts

### 16.1 WebSocket Endpoints

| Path | Auth | Purpose | Direction |
|---|---|---|---|
| `/ws/ai/runs/{run_id}` | JWT | Real-time run progress | Server → Client |
| `/ws/ai/conversations/{conv_id}` | JWT | Streaming chat responses | Bidirectional |
| `/ws/ai/notifications` | JWT | AI completion alerts | Server → Client |

### 16.2 Run Progress Stream

```json
// Server → Client: Run progress update
{
  "type": "run.progress",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress_pct": 45,
  "current_step": "Generating lesson plan objectives...",
  "timestamp": "2026-06-09T07:30:00Z"
}

// Server → Client: Run completed
{
  "type": "run.completed",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "output_id": "660e8400-e29b-41d4-a716-446655440001",
  "review_state": "pending",
  "cost_cents": 0.45,
  "latency_ms": 8500,
  "timestamp": "2026-06-09T07:30:08Z"
}

// Server → Client: Run failed
{
  "type": "run.failed",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "error_type": "llm_timeout",
  "error_message": "LLM request timed out after 120s",
  "retryable": true,
  "timestamp": "2026-06-09T07:32:00Z"
}
```

### 16.3 Streaming Chat

```json
// Client → Server: Send message
{
  "type": "message.send",
  "conversation_id": "770e8400-e29b-41d4-a716-446655440002",
  "content": "Create a lesson plan for Grade 3 Mathematics, Fractions"
}

// Server → Client: Streaming chunk
{
  "type": "message.chunk",
  "conversation_id": "770e8400-e29b-41d4-a716-446655440002",
  "message_id": "880e8400-e29b-41d4-a716-446655440003",
  "delta": "Here is a lesson plan for Grade 3 Mathematics on Fractions...",
  "finish_reason": null
}

// Server → Client: Stream complete
{
  "type": "message.complete",
  "conversation_id": "770e8400-e29b-41d4-a716-446655440002",
  "message_id": "880e8400-e29b-41d4-a716-446655440003",
  "content": "Here is a lesson plan for Grade 3 Mathematics on Fractions...",
  "tool_calls": [],
  "token_usage": {
    "prompt_tokens": 1250,
    "completion_tokens": 890,
    "total_tokens": 2140
  },
  "cost_cents": 0.12
}

// Server → Client: Tool call in progress
{
  "type": "tool.calling",
  "conversation_id": "770e8400-e29b-41d4-a716-446655440002",
  "tool_name": "curriculum_search",
  "arguments": {"subject": "Mathematics", "grade": 3, "topic": "Fractions"}
}

// Server → Client: Tool result
{
  "type": "tool.result",
  "conversation_id": "770e8400-e29b-41d4-a716-446655440002",
  "tool_name": "curriculum_search",
  "success": true,
  "result_count": 5
}
```

### 16.4 Notification Stream

```json
// Server → Client: AI output ready for review
{
  "type": "ai.output.ready",
  "output_id": "990e8400-e29b-41d4-a716-446655440004",
  "agent_kind": "lesson_planning",
  "review_state": "pending",
  "domain_type": "lesson_plan",
  "created_by_name": "Maria Santos",
  "timestamp": "2026-06-09T07:35:00Z"
}

// Server → Client: Budget alert
{
  "type": "ai.budget.alert",
  "alert_level": "warning",
  "current_spend_cents": 4000.00,
  "budget_limit_cents": 5000.00,
  "usage_pct": 80.0,
  "period": "monthly"
}
```

---

## 17. Folder Structure

```text
backend/src/
├── domains/
│   └── ai/                          # AI Bounded Context (Domain Layer)
│       ├── __init__.py
│       ├── agents/                   # Agent implementations
│       │   ├── __init__.py
│       │   ├── base_agent.py         # Abstract BaseAgent
│       │   ├── lesson_planning_agent.py
│       │   ├── assessment_agent.py
│       │   ├── gradebook_agent.py
│       │   ├── forms_agent.py
│       │   ├── student_risk_agent.py
│       │   ├── report_agent.py
│       │   └── communication_agent.py
│       ├── tools/                    # Tool definitions
│       │   ├── __init__.py
│       │   ├── base_tool.py          # Abstract AITool
│       │   ├── curriculum_search.py
│       │   ├── melc_lookup.py
│       │   ├── student_search.py
│       │   ├── attendance_analyzer.py
│       │   ├── grade_lookup.py
│       │   ├── rubric_generator.py
│       │   ├── form_template_lookup.py
│       │   ├── notification_sender.py
│       │   ├── student_risk_score.py
│       │   └── form_validator.py
│       ├── value_objects/            # AI value objects
│       │   ├── __init__.py
│       │   ├── agent_kind.py
│       │   ├── model_config.py
│       │   ├── token_usage.py
│       │   ├── cost_breakdown.py
│       │   └── review_state.py
│       ├── events/                   # AI domain events
│       │   ├── __init__.py
│       │   ├── ai_run_started.py
│       │   ├── ai_run_completed.py
│       │   ├── ai_run_failed.py
│       │   ├── ai_output_generated.py
│       │   ├── ai_output_reviewed.py
│       │   ├── ai_feedback_submitted.py
│       │   └── ai_budget_alert.py
│       ├── repos/                    # Repository interfaces
│       │   ├── __init__.py
│       │   ├── agent_run_repo.py
│       │   ├── ai_output_repo.py
│       │   ├── prompt_repo.py
│       │   └── conversation_repo.py
│       ├── services/                 # Domain services
│       │   ├── __init__.py
│       │   ├── agent_runner.py       # Orchestrates agent execution
│       │   ├── review_gate.py        # Human-in-the-loop logic
│       │   ├── cost_calculator.py    # Cost computation
│       │   └── output_manager.py     # Output versioning/superseding
│       └── workflow/                 # AI workflow configuration
│           ├── __init__.py
│           ├── ai_workflow_config.py
│           └── review_workflow.py
│
├── application/ai/                   # Application Layer (Use Cases)
│   ├── __init__.py
│   ├── run_agent_use_case.py
│   ├── review_output_use_case.py
│   ├── manage_prompt_use_case.py
│   ├── manage_conversation_use_case.py
│   └── get_cost_dashboard_use_case.py
│
├── infrastructure/ai/                # Infrastructure Layer
│   ├── __init__.py
│   ├── providers/                    # LLM Provider implementations
│   │   ├── __init__.py
│   │   ├── base_provider.py          # Abstract AIProvider
│   │   ├── openai_provider.py        # OpenAI API client
│   │   ├── anthropic_provider.py     # Anthropic API client
│   │   ├── ollama_provider.py        # Local Ollama client
│   │   └── fake_provider.py          # Mock provider for testing
│   ├── tools/                        # Tool registry + implementations
│   │   ├── __init__.py
│   │   ├── tool_registry.py
│   │   └── tool_executor.py
│   ├── prompts/                      # Prompt management
│   │   ├── __init__.py
│   │   ├── prompt_registry.py
│   │   └── template_engine.py
│   ├── memory/                       # Memory subsystem
│   │   ├── __init__.py
│   │   ├── working_memory.py         # Redis-backed
│   │   └── conversation_memory.py    # PostgreSQL-backed
│   ├── rag/                          # RAG subsystem
│   │   ├── __init__.py
│   │   ├── vector_store.py
│   │   ├── embedding_service.py
│   │   ├── chunker.py
│   │   └── retrieval_pipeline.py
│   ├── security/                     # AI security
│   │   ├── __init__.py
│   │   ├── prompt_guard.py
│   │   ├── output_validator.py
│   │   └── pii_detector.py
│   ├── cost/                         # Cost tracking
│   │   ├── __init__.py
│   │   ├── cost_tracker.py
│   │   ├── budget_manager.py
│   │   └── pricing_calculator.py
│   ├── db/                           # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── ai_models.py
│   │   └── ai_repositories.py
│   └── tracing.py                    # OpenTelemetry tracing
│
├── api/v1/ai/                        # API Layer (FastAPI Routers)
│   ├── __init__.py
│   ├── agents.py                     # /api/v1/ai/agents
│   ├── runs.py                       # /api/v1/ai/runs
│   ├── outputs.py                    # /api/v1/ai/outputs
│   ├── prompts.py                    # /api/v1/ai/prompts
│   ├── conversations.py              # /api/v1/ai/conversations
│   ├── costs.py                      # /api/v1/ai/costs
│   ├── feedback.py                   # /api/v1/ai/feedback
│   └── knowledge.py                  # /api/v1/ai/knowledge
│
├── api/ws/ai/                        # WebSocket handlers
│   ├── __init__.py
│   ├── run_stream.py                 # /ws/ai/runs/{run_id}
│   ├── chat_stream.py                # /ws/ai/conversations/{conv_id}
│   └── notification_stream.py        # /ws/ai/notifications
│
├── schemas/ai/                       # Pydantic request/response models
│   ├── __init__.py
│   ├── agent_schemas.py
│   ├── run_schemas.py
│   ├── output_schemas.py
│   ├── prompt_schemas.py
│   ├── conversation_schemas.py
│   ├── cost_schemas.py
│   └── feedback_schemas.py
│
├── tasks/ai/                         # Celery task modules
│   ├── __init__.py
│   ├── generation.py                 # AI generation tasks
│   ├── embedding.py                  # RAG embedding tasks
│   ├── evaluation.py                 # Batch evaluation tasks
│   └── cost_rollup.py               # Daily cost aggregation
│
├── events/handlers/ai/               # Event handlers
│   ├── __init__.py
│   ├── ai_event_handlers.py          # Handle AI domain events
│   └── domain_ai_consumers.py        # Consume domain events for AI
│
└── observability/
    └── ai_metrics.py                 # AI-specific Prometheus metrics
```

---

## 18. Sequence Diagrams

### 18.1 AI Lesson Plan Generation (with Human-in-the-Loop)

```
Teacher          FastAPI          AgentRunner       LLM Provider     AgentRun       AIOutput        Workflow        EventBus
  │                │                  │                  │              │              │               │               │
  │ POST /ai/agents/lesson_planning/run │              │              │              │               │               │
  │───────────────►│                  │                  │              │              │               │               │
  │                │ validate RBAC    │                  │              │              │               │               │
  │                │ check budget     │                  │              │              │               │               │
  │                │                  │                  │              │              │               │               │
  │                │ run_agent(context)│                 │              │              │               │               │
  │                │─────────────────►│                  │              │              │               │               │
  │                │                  │                  │              │              │               │               │
  │                │                  │ INSERT agent_run │              │              │               │               │
  │                │                  │ (status=queued)  │              │              │               │               │
  │                │                  │──────────────────────────────►  │              │               │               │
  │                │                  │                  │              │              │               │               │
  │                │                  │ load_prompt()    │              │              │               │               │
  │                │                  │ build_messages() │              │              │               │               │
  │                │                  │ retrieve_rag()   │              │              │               │               │
  │                │                  │                  │              │              │               │               │
  │                │                  │ chat(messages)   │              │              │               │               │
  │                │                  │─────────────────►│              │              │               │               │
  │                │                  │                  │              │              │               │               │
  │                │                  │    raw_response  │              │              │               │               │
  │                │                  │◄─────────────────│              │              │               │               │
  │                │                  │                  │              │              │               │               │
  │                │                  │ parse_response() │              │              │               │               │
  │                │                  │ validate_output()│              │              │               │               │
  │                │                  │                  │              │              │               │               │
  │                │                  │ INSERT ai_output │              │              │               │               │
  │                │                  │ (review_state=pending)          │              │               │               │
  │                │                  │────────────────────────────────────────────►  │               │               │
  │                │                  │                  │              │              │               │               │
  │                │                  │ UPDATE agent_run │              │              │               │               │
  │                │                  │ (status=completed, output_id)  │              │               │               │
  │                │                  │──────────────────────────────►  │              │               │               │
  │                │                  │                  │              │              │               │               │
  │                │                  │ publish(AIOutputGenerated)      │              │               │               │
  │                │                  │──────────────────────────────────────────────────────────────►│               │
  │                │                  │                  │              │              │               │               │
  │                │ 200 OK (output_id, review_state=pending)         │              │               │               │
  │                │◄─────────────────│                  │              │              │               │               │
  │◄───────────────│                  │                  │              │              │               │               │
  │                │                  │                  │              │              │               │               │
  │ [Teacher reviews output]         │                  │              │              │               │               │
  │                │                  │                  │              │              │               │               │
  │ POST /ai/outputs/{id}/approve    │                  │              │              │               │               │
  │───────────────►│                  │                  │              │              │               │               │
  │                │ UPDATE ai_output │                  │              │              │               │               │
  │                │ (review_state=approved)             │              │              │               │               │
  │                │────────────────────────────────────────────────►  │              │               │               │
  │                │                  │                  │              │              │               │               │
  │                │ publish(AIOutputReviewed)           │              │              │               │               │
  │                │─────────────────────────────────────────────────────────────────────────────────►               │
  │                │                  │                  │              │              │               │               │
  │                │                  │ apply_ai_output() via domain service                            │               │
  │                │                  │───────────────────────────────────────────────────────────────────────────►  │
  │                │                  │                  │              │              │               │               │
```

### 18.2 AI Risk Assessment Evaluation

```
Scheduler       RiskService       AgentRunner       StudentRiskAgent    LLM        RiskAssessment    InterventionService   CommsService
  │                │                  │                  │               │              │               │                  │
  │ evaluate_all() │                  │                  │               │              │               │                  │
  │───────────────►│                  │                  │               │              │               │                  │
  │                │ SELECT students  │                  │               │              │               │                  │
  │                │ + attendance     │                  │               │              │               │                  │
  │                │ + grades         │                  │               │              │               │                  │
  │                │                  │                  │               │              │               │                  │
  │                │ run_agent(student_data)             │               │              │               │                  │
  │                │─────────────────►│                  │               │              │               │                  │
  │                │                  │ run(student_risk)│               │              │               │                  │
  │                │                  │─────────────────►│               │              │               │                  │
  │                │                  │                  │ build_messages│              │               │                  │
  │                │                  │                  │ + RAG context │              │               │                  │
  │                │                  │                  │──────────────►│              │               │                  │
  │                │                  │                  │    response   │              │               │                  │
  │                │                  │                  │◄──────────────│              │               │                  │
  │                │                  │                  │ parse + validate             │               │                  │
  │                │                  │                  │               │              │               │                  │
  │                │                  │  output {overall_score, category_scores, reasoning, recommendations} │
  │                │                  │◄─────────────────│               │              │               │                  │
  │                │                  │                  │               │              │               │                  │
  │                │ INSERT risk_assessment              │               │              │               │                  │
  │                │ (ai_generated=TRUE, ai_run_id)      │               │              │               │                  │
  │                │────────────────────────────────────────────────►  │              │               │                  │
  │                │                  │                  │               │              │               │                  │
  │                │ [if score >= high_threshold]        │               │              │               │                  │
  │                │ create_intervention_case()          │               │              │               │                  │
  │                │──────────────────────────────────────────────────────────────────►│                  │
  │                │                  │                  │               │              │               │                  │
  │                │ notify_teacher() │                  │               │              │               │                  │
  │                │──────────────────────────────────────────────────────────────────────────────────►│
  │                │                  │                  │               │              │               │                  │
  │                │ publish(InterventionCreated)        │               │              │               │                  │
  │                │─────────────────────────────────────────────────────────────────────────────────────────────────►
```

### 18.3 RAG Knowledge Retrieval + Generation

```
Agent           VectorStore       pgvector          EmbeddingService   LLM
  │                │                  │                  │              │
  │ get_rag_query()│                  │                  │              │
  │ (returns query │                  │                  │              │
  │  like "Grade 3 │                  │                  │              │
  │  fractions     │                  │                  │              │
  │  MELC")        │                  │                  │              │
  │                │                  │                  │              │
  │ search(query)  │                  │                  │              │
  │───────────────►│                  │                  │              │
  │                │ embed(query)     │                  │              │
  │                │─────────────────►│                  │              │
  │                │    vector        │                  │              │
  │                │◄─────────────────│                  │              │
  │                │                  │                  │              │
  │                │ HNSW search      │                  │              │
  │                │ (cosine sim,     │                  │              │
  │                │  top_k=10,       │                  │              │
  │                │  tenant-scoped)  │                  │              │
  │                │─────────────────►│                  │              │
  │                │    chunks[]      │                  │              │
  │                │◄─────────────────│                  │              │
  │                │                  │                  │              │
  │  chunks[]      │                  │                  │              │
  │◄───────────────│                  │                  │              │
  │                │                  │                  │              │
  │ build_messages │                  │                  │              │
  │ (inject chunks │                  │                  │              │
  │  into context) │                  │                  │              │
  │                │                  │                  │              │
  │ chat(messages + RAG context)      │                  │              │
  │──────────────────────────────────────────────────────────────────►│
  │                │                  │                  │    response  │
  │                │                  │                  │◄─────────────│
```

### 18.4 AI Form Auto-Generation

```
Teacher          FormsAgent        FormService       LLM         SchoolForm      FormValidator
  │                │                  │                │              │               │
  │ POST /ai/agents/forms/run        │                │              │               │
  │ (domain_type=school_form,        │                │              │               │
  │  domain_data={form_code: "SF9",  │                │              │               │
  │  school_year: "2026-2027",       │                │              │               │
  │  quarter: 1})                    │                │              │               │
  │───────────────►│                  │                │              │               │
  │                │ load template    │                │              │               │
  │                │ (form_code)      │                │              │               │
  │                │─────────────────►│                │              │               │
  │                │    template      │                │              │               │
  │                │◄─────────────────│                │              │               │
  │                │                  │                │              │               │
  │                │ load data        │                │              │               │
  │                │ (attendance,     │                │              │               │
  │                │  grades, etc.)   │                │              │               │
  │                │─────────────────►│                │              │               │
  │                │    domain_data   │                │              │               │
  │                │◄─────────────────│                │              │               │
  │                │                  │                │              │               │
  │                │ chat(template + data)             │              │               │
  │                │──────────────────────────────────►│              │               │
  │                │    form_content  │                │              │               │
  │                │◄──────────────────────────────────│              │               │
  │                │                  │                │              │               │
  │                │ validate(form_content)            │              │               │
  │                │─────────────────────────────────────────────────────────────────►│
  │                │    validation_result             │              │               │
  │                │◄─────────────────────────────────────────────────────────────────│
  │                │                  │                │              │               │
  │                │ INSERT school_form + version      │              │               │
  │                │─────────────────►│                │              │               │
  │                │                  │────────────────────────────────►              │
  │                │                  │                │              │               │
  │ 200 OK (output_id, form_id)      │                │              │               │
  │◄───────────────│                  │                │              │               │
```

### 18.5 Multi-Turn AI Conversation

```
Teacher          FastAPI           ConversationMemory  WorkingMemory(Redis)   LLM
  │                │                  │                    │                    │
  │ WS: message.send                  │                    │                    │
  │───────────────►│                  │                    │                    │
  │                │                  │                    │                    │
  │                │ get_working_memory(tenant, conv_id)   │                    │
  │                │──────────────────────────────────────►│                    │
  │                │    history[]     │                    │                    │
  │                │◄──────────────────────────────────────│                    │
  │                │                  │                    │                    │
  │                │ build_messages(history + new_message) │                    │
  │                │                  │                    │                    │
  │                │ chat(messages)   │                    │                    │
  │────────────────────────────────────────────────────────────────────────────►│
  │                │                  │                    │    stream chunks   │
  │ WS: message.chunk (multiple)      │                    │◄───────────────────│
  │◄───────────────│                  │                    │                    │
  │                │                  │                    │                    │
  │ WS: message.complete              │                    │                    │
  │◄───────────────│                  │                    │                    │
  │                │                  │                    │                    │
  │                │ save_working_memory(tenant, conv_id, new_messages)         │
  │                │──────────────────────────────────────►│                    │
  │                │                  │                    │ (TTL=30min)        │
  │                │                  │                    │                    │
  │                │ INSERT ai_messages (user + assistant) │                    │
  │                │─────────────────►│                    │                    │
  │                │                  │                    │                    │
  │                │ UPDATE conversation (message_count++) │                    │
  │                │─────────────────►│                    │                    │
```

### 18.6 AI Report Summary Generation

```
Teacher          ReportAgent       ComplianceService  LLM        AIOutput       ReportService
  │                │                  │                 │             │               │
  │ POST /ai/agents/report/run       │                 │             │               │
  │ (domain_type="report",           │                 │             │               │
  │  domain_data={report_type:       │                 │             │               │
  │  "quarterly_accomplishment"})    │                 │             │               │
  │───────────────►│                  │                 │             │               │
  │                │ gather_data()    │                 │             │               │
  │                │─────────────────►│                 │             │               │
  │                │    report_data   │                 │             │               │
  │                │◄─────────────────│                 │             │               │
  │                │                  │                 │             │               │
  │                │ chat(summary_prompt + data)        │             │               │
  │                │───────────────────────────────────►│             │               │
  │                │    summary      │                 │             │               │
  │                │◄───────────────────────────────────│             │               │
  │                │                  │                 │             │               │
  │                │ INSERT ai_output│                 │             │               │
  │                │ (domain_type=report)               │             │               │
  │                │────────────────────────────────────────────────►│               │
  │                │                  │                 │             │               │
  │ [Teacher reviews and approves]   │                 │             │               │
  │                │                  │                 │             │               │
  │                │ apply_to_report()│                 │             │               │
  │                │───────────────────────────────────────────────────────────────►│
  │                │                  │                 │             │    report     │
  │                │                  │                 │             │◄──────────────│
```

### 18.7 AI Communication Draft

```
Teacher          CommunicationAgent   CommsService    LLM        AIOutput       NotificationService
  │                │                     │              │             │               │
  │ POST /ai/agents/communication/run   │              │             │               │
  │ (domain_data={                       │              │             │               │
  │   student_id, parent_id,            │              │             │               │
  │   subject: "Academic Performance",  │              │             │               │
  │   context: "low grades in Math"     │              │             │               │
  │ })                                   │              │             │               │
  │───────────────►│                     │              │             │               │
  │                │ lookup student data │              │             │               │
  │                │ lookup parent info  │              │             │               │
  │                │ lookup grade data   │              │             │               │
  │                │                     │              │             │               │
  │                │ chat(draft_prompt + context)       │             │               │
  │                │───────────────────────────────────►│             │               │
  │                │    draft message    │              │             │               │
  │                │◄───────────────────────────────────│             │               │
  │                │                     │              │             │               │
  │                │ tone_check (formal, empathetic,    │             │               │
  │                │ culturally appropriate)             │             │               │
  │                │                     │              │             │               │
  │                │ INSERT ai_output   │              │             │               │
  │                │ (review_state=pending, risk=high)  │             │               │
  │                │────────────────────────────────────────────────►│               │
  │                │                     │              │             │               │
  │ [Teacher reviews, edits, approves]  │              │             │               │
  │                │                     │              │             │               │
  │                │ send_message()      │              │             │               │
  │                │───────────────────────────────────────────────────────────────►│
  │                │                     │              │             │  sms/email    │
  │                │                     │              │             │  sent to      │
  │                │                     │              │             │  parent       │
```

---

## 19. Deployment Architecture

### 19.1 MVP — Docker Compose

```yaml
# docker-compose.ai.yml (extends base docker-compose.yml)
version: "3.9"
services:
  # --- Existing services (from base) ---
  db:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes: ["db_data:/var/lib/postgresql/data"]
    # pgvector extension installed automatically

  redis:
    image: redis:7-alpine

  # --- AI Services ---
  api:
    build: .
    command: uvicorn backend.src.main:app --host 0.0.0.0 --port 8000
    depends_on: [db, redis]
    ports: ["8000:8000"]
    env_file: .env
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

  # AI worker — dedicated queue for AI tasks
  ai-worker:
    build: .
    command: >
      celery -A backend.src.infrastructure.message_queue.celery_app worker
      -Q ai,ai_generation
      --concurrency=4
      --max-tasks-per-child=100
    depends_on: [db, redis]
    env_file: .env
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CELERY_CONCURRENCY=4

  # Background tasks — existing queues
  worker:
    build: .
    command: celery -A backend.src.infrastructure.message_queue.celery_app worker -Q default,gradebook,forms
    depends_on: [db, redis]
    env_file: .env

  beat:
    build: .
    command: celery -A backend.src.infrastructure.message_queue.celery_app beat
    depends_on: [db, redis]

volumes:
  db_data:
```

### 19.2 Production — Kubernetes

```yaml
# AI Worker Deployment (Helm values)
aiWorker:
  replicaCount: 2
  queue: ai,ai_generation
  concurrency: 4
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "1Gi"
      cpu: "1000m"
  autoscaling:
    enabled: true
    minReplicas: 1
    maxReplicas: 10
    targetQueueDepth: 10  # Scale up when >10 tasks in queue
  env:
    - name: OPENAI_API_KEY
      valueFrom:
        secretKeyRef:
          name: ai-secrets
          key: openai-api-key
```

### 19.3 LLM Provider Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                  LLM Provider Strategy                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PRIMARY: OpenAI (gpt-4o, gpt-4o-mini)                      │
│  ├── Best quality/cost ratio for educational content         │
│  ├── Structured output support                               │
│  ├── Function calling for tools                              │
│  └── Prompt caching for cost savings                         │
│                                                              │
│  FALLBACK: Anthropic (claude-3.5-sonnet, claude-3-haiku)     │
│  ├── Used when OpenAI is rate-limited or down                │
│  ├── Excellent for long-form educational content             │
│  └── Strong safety alignment                                 │
│                                                              │
│  SELF-HOSTED: Ollama (future)                                │
│  ├── For schools with connectivity issues                    │
│  ├── For data that cannot leave premises                     │
│  └── llama3.1, mistral for simpler tasks                     │
│                                                              │
│  PROVIDER ABSTRACTION:                                       │
│  ├── All agents use AIProvider interface                     │
│  ├── Provider switching is transparent                       │
│  └── Cost tracking per provider                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 19.4 Caching Strategy

```python
AI_CACHE_CONFIG = {
    # Response cache — same input produces same output
    "response_cache_ttl": 3600,  # 1 hour
    "response_cache_prefix": "ai:response",

    # Embedding cache — avoid re-embedding same text
    "embedding_cache_ttl": 86400,  # 24 hours
    "embedding_cache_prefix": "ai:embedding",

    # Prompt cache — LLM provider-side prompt caching
    "enable_prompt_caching": True,  # OpenAI prompt caching
    "cache_control_header": True,   # Anthropic cache_control
}
```

---

## 20. Testing Strategy

### 20.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  5% — Full workflow tests
                   ┌┴─────────┴┐
                   │ Integration │  15% — API + DB + mocked LLM
                  ┌┴───────────┴┐
                  │  Contract    │  10% — OpenAPI validation
                 ┌┴─────────────┴┐
                 │   Component    │  20% — Agent + Tool + Memory
                ┌┴───────────────┴┐
                │     Unit         │  50% — Pure logic, value objects
                └─────────────────┘
```

### 20.2 Mock LLM Provider

```python
# backend/src/infrastructure/ai/providers/fake_provider.py
from typing import Any, Dict, List

from .base_provider import AIProvider


class FakeLLMProvider(AIProvider):
    """Deterministic LLM provider for testing.

    Allows tests to pre-program responses and verify
    that agents call the LLM with expected messages.
    """

    def __init__(self) -> None:
        self._responses: Dict[str, str] = {}
        self._call_history: List[Dict[str, Any]] = []

    def program_response(self, agent_kind: str, response: str) -> None:
        """Pre-program a response for a given agent kind."""
        self._responses[agent_kind] = response

    async def chat(self, messages: List[Dict], model_config: Any) -> str:
        self._call_history.append({
            "messages": messages,
            "model": model_config.model_name,
        })
        agent_kind = messages[0].get("metadata", {}).get("agent_kind", "default")
        return self._responses.get(agent_kind, '{"error": "no programmed response"}')

    async def chat_stream(self, messages: List[Dict], model_config: Any):
        response = await self.chat(messages, model_config)
        yield response

    @property
    def call_count(self) -> int:
        return len(self._call_history)

    @property
    def last_call(self) -> Dict[str, Any]:
        return self._call_history[-1] if self._call_history else {}

    def reset(self) -> None:
        self._responses.clear()
        self._call_history.clear()
```

### 20.3 Test Categories

| Type | Scope | Tools | Example |
|---|---|---|---|
| **Unit** | Value objects, cost calculation, prompt guard, tool schemas | `pytest`, `pytest-asyncio` | Test `TokenUsage.cache_hit_rate`, `PromptInjectionGuard.detect()` |
| **Component** | Agent build_messages, parse_response, tool execution | `pytest` + `FakeLLMProvider` | Test `LessonPlanningAgent.build_messages()` with mocked RAG |
| **Integration** | Full AI run with mocked LLM, DB via testcontainers | `pytest` + `testcontainers-postgres` + `testcontainers-redis` | Test `run_agent_use_case.execute()` end-to-end |
| **Contract** | OpenAPI spec validation | `schemathesis` | Validate all `/api/v1/ai/*` endpoints against OpenAPI |
| **E2E** | Complete workflow: create → AI generate → review → approve | `playwright` or `httpx` | Test lesson plan creation with AI generation |
| **Security** | Prompt injection, tenant isolation, PII detection | `pytest` | Attempt cross-tenant data access, injection attacks |
| **Performance** | Concurrent AI runs, vector search benchmarks | `locust`, custom async scripts | 50 concurrent runs, vector search latency <100ms |
| **Quality** | AI output quality regression | Custom scoring + golden dataset | Compare new prompt version output against baseline |

### 20.4 Test File Structure

```text
backend/src/tests/
├── ai/
│   ├── unit/
│   │   ├── test_value_objects.py
│   │   ├── test_cost_calculator.py
│   │   ├── test_prompt_guard.py
│   │   ├── test_pii_detector.py
│   │   ├── test_template_engine.py
│   │   └── test_tool_schemas.py
│   ├── component/
│   │   ├── test_lesson_planning_agent.py
│   │   ├── test_assessment_agent.py
│   │   ├── test_student_risk_agent.py
│   │   ├── test_forms_agent.py
│   │   ├── test_gradebook_agent.py
│   │   ├── test_report_agent.py
│   │   ├── test_communication_agent.py
│   │   ├── test_tool_registry.py
│   │   └── test_tool_executor.py
│   ├── integration/
│   │   ├── test_run_agent_flow.py
│   │   ├── test_review_flow.py
│   │   ├── test_conversation_flow.py
│   │   ├── test_rag_pipeline.py
│   │   ├── test_cost_tracking.py
│   │   └── test_prompt_lifecycle.py
│   ├── contract/
│   │   ├── test_ai_api_openapi.py
│   │   └── test_websocket_contracts.py
│   ├── security/
│   │   ├── test_prompt_injection.py
│   │   ├── test_tenant_isolation.py
│   │   ├── test_pii_leakage.py
│   │   └── test_rate_limiting.py
│   └── e2e/
│       ├── test_lesson_plan_ai_flow.py
│       ├── test_risk_assessment_flow.py
│       └── test_form_generation_flow.py
│   └── fixtures/
│       ├── sample_lesson_plan_output.json
│       ├── sample_risk_assessment_output.json
│       ├── sample_melc_data.json
│       └── test_prompts/
```

### 20.5 Golden Dataset for Quality Regression

```python
# backend/src/tests/ai/fixtures/golden_dataset.py
"""Golden dataset for AI output quality regression testing.

Each entry contains:
- input: The domain context provided to the agent
- expected_schema: JSON Schema the output must conform to
- quality_threshold: Minimum quality score (0-1) for the output
- baseline_output: The reference output from the last known-good version
"""

GOLDEN_DATASET = [
    {
        "agent_kind": "lesson_planning",
        "name": "Grade 3 Mathematics - Fractions",
        "input": {
            "grade_level": "Grade 3",
            "subject": "Mathematics",
            "topic": "Introduction to Fractions",
            "duration_minutes": 60,
        },
        "quality_threshold": 0.8,
    },
    {
        "agent_kind": "assessment",
        "name": "Grade 5 Science - Quiz (10 items)",
        "input": {
            "grade_level": "Grade 5",
            "subject": "Science",
            "topic": "States of Matter",
            "num_items": 10,
            "item_types": ["multiple_choice", "true_false", "short_answer"],
        },
        "quality_threshold": 0.75,
    },
    {
        "agent_kind": "student_risk",
        "name": "High-risk student identification",
        "input": {
            "students": [
                {"name": "Test Student", "attendance_rate": 0.45, "avg_grade": 72},
            ],
        },
        "quality_threshold": 0.85,
    },
]
```

### 20.6 CI Pipeline

```yaml
# .github/workflows/ai-tests.yml
name: AI Platform Tests
on: [push, pull_request]

jobs:
  ai-unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run AI unit tests
        run: pytest backend/src/tests/ai/unit/ -v --cov=backend/src/domains/ai --cov=backend/src/infrastructure/ai --cov-report=xml

  ai-component-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run AI component tests
        run: pytest backend/src/tests/ai/component/ -v

  ai-integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg15
        env:
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
      redis:
        image: redis:7
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - name: Run AI integration tests
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379
        run: pytest backend/src/tests/ai/integration/ -v

  ai-security-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run AI security tests
        run: pytest backend/src/tests/ai/security/ -v
```

---

## Appendix A: Environment Variables

```env
# AI Platform Configuration
AI_DEFAULT_PROVIDER=openai
AI_DEFAULT_MODEL=gpt-4o
AI_FALLBACK_PROVIDER=anthropic
AI_FALLBACK_MODEL=claude-3.5-sonnet

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_BASE_URL=http://localhost:11434

# AI Budget Defaults
AI_MONTHLY_BUDGET_CENTS=5000
AI_DAILY_BUDGET_CENTS=500
AI_PER_RUN_BUDGET_CENTS=100

# AI Rate Limiting
AI_USER_RATE_LIMIT_PER_MINUTE=10
AI_TENANT_RATE_LIMIT_PER_MINUTE=50

# RAG Configuration
AI_EMBEDDING_MODEL=text-embedding-3-small
AI_EMBEDDING_DIMENSIONS=1536
AI_RAG_CHUNK_SIZE=512
AI_RAG_CHUNK_OVERLAP=64
AI_RAG_TOP_K=10
AI_RAG_SIMILARITY_THRESHOLD=0.7

# Memory
AI_WORKING_MEMORY_TTL=1800
AI_CONVERSATION_MAX_MESSAGES=50

# Observability
AI_TRACE_ENABLED=true
AI_LOG_LEVEL=info
```

## Appendix B: RBAC Permission Matrix

| Permission | Teacher | Principal | Guidance | Admin | DepEd Staff |
|---|---|---|---|---|---|
| `ai.run` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ai.run.risk_assessment` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `ai.run.report_generation` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ai.review` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ai.approve` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ai.reject` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ai.edit_output` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ai.prompts.read` | ❌ | ❌ | ❌ | ✅ | ✅ |
| `ai.prompts.write` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `ai.prompts.publish` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `ai.agents.manage` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `ai.budget.view` | ❌ | ✅ | ❌ | ✅ | ✅ |
| `ai.budget.manage` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `ai.knowledge.read` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ai.knowledge.write` | ❌ | ❌ | ❌ | ✅ | ❌ |

## Appendix C: OpenADR / DepEd Compliance Notes

- All AI-generated DepEd forms include a provenance footnote: "Generated by TeacherOS AI on [date], Model: [model], Prompt Version: [v#]"
- AI outputs for RPMS (reporting) are always marked as `ai_generated = TRUE` for transparency
- Risk assessments include `human_validated` flag — DepEd requires human sign-off
- AI cost tracking supports DepEd budget reporting requirements for ICT spending

---

*This document is version-controlled alongside the SQL schema. Reference it from the project README and use it as the source of truth for all AI implementation decisions.*