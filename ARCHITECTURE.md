# TeacherOS – Backend Architecture Blueprint

This document provides a complete, production‑ready design for the **Teacher Operating System (TeacherOS)** backend.  It aligns with the existing SQL schema in the `architecture/` folder (`01‑auth‑organization.sql`, `02‑student‑information.sql`, … `06‑school‑forms.sql`) and follows Domain‑Driven Design, Clean Architecture, and SOLID principles.

---

## 1️⃣ High‑Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENTS (Web / Mobile)                    │
│   • Teacher portal • Parent portal • Admin console • Mobile apps │
└───────────────▲───────────────────────▲──────────────────────────┘
                │ HTTPS (TLS 1.3)   │ WebSocket (wss)
                │                  │
 ┌──────────────▼───────────────────────▼───────────────────────────┐
 │               API GATEWAY / LOAD BALANCER (Envoy)               │
 │  • TLS termination • Rate‑limiting • HTTP → FastAPI • WS → WS   │
 └──────▲───────────────────────▲───────────────────────▲─────────┘
        │                           │                       │
 ┌──────▼───────┐          ┌────────▼───────┐   ┌───────────▼───────┐
 │ FastAPI (API)│          │ FastAPI WS    │   │   Event Bus      │
 │   – Routers   │          │ – Notifications│   │ (Kafka / Redis) │
 └──────▲───────┘          └──────▲───────┘   └──────▲───────▲────┘
        │                         │                │       │
        │                         │                │       │
 ┌──────▼───────┐          ┌──────▼─────┐   ┌──────▼─────┐ │
 │ Application  │          │  Workers   │   │  Infra‑   │ │
 │ Layer (Use‑ │          │ (Celery)   │   │  structure│ │
 │ Cases)      │          └──────▲─────┘   └──────▲─────┘ │
 └──────▲───────┘                 │                │       │
        │                         │                │       │
 ┌──────▼───────┐          ┌──────▼─────┐   ┌──────▼─────┐ │
 │ Domain Layer │          │  Cache     │   │  DB (Postgres)│ │
 │ (Entities,   │          │ (Redis)    │   │  + RLS       │ │
 │  Services)  │          └──────▲─────┘   └──────▲─────┘ │
 └──────▲───────┘                 │                │       │
        │                         │                │       │
 ┌──────▼───────┐          ┌──────▼─────┐   ┌──────▼─────┐ │
 │ Cross‑Cutting│          │  Storage   │   │  Search    │ │
 │ (Logging,   │          │ (S3/Supabase)│ │ (Postgres FT│ │
 │ Metrics, etc)│          └──────▲─────┘   └──────▲─────┘ │
 └─────────────┘                 │                │       │
                                 │                │       │
                         ┌───────▼───────┐   ┌────▼─────┐
                         │  Observability│   │  Queue   │
                         │ (Prom/Grafana)│   │ (Celery) │
                         └───────────────┘   └──────────┘
```

All services are containerised (Docker) and can be scaled horizontally. The **Event Bus** decouples domains and powers the generic workflow engine.

---

## 2️⃣ Domain‑Driven Design (DDD) Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Identity      │    │   Student       │    │   Lesson        │
│   (users,roles)│◄──►│   (students…)  │◄──►│   (DLL, MELC)   │
└─────▲─────▲─────┘    └─────▲─────▲─────┘    └─────▲─────▲─────┘
      │     │                │     │                │     │
      │     │                │     │                │     │
      ▼     ▼                ▼     ▼                ▼     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────────┐
│ Assessment    │   │ Gradebook       │   │ Forms                │
│ (quizzes…)   │   │ (scores,report)│   │ (SF1‑SF10)           │
└────▲─────▲─────┘   └────▲──────▲─────┘   └─────▲─────▲───────────┘
       │    │              │      │               │     │
       │    │              │      │               │     │
       ▼    ▼              ▼      ▼               ▼     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────────┐
│ Communication │   │ Reporting       │   │ AI / Agents         │
│ (messages)    │   │ (RPMS, etc.)    │   │ (lesson,grade…)    │
└─────▲─────▲───┘   └─────▲─────▲──────┘   └─────▲─────▲─────────┘
      │     │           │     │                │     │
      │     │           │     │                │     │
      ▼     ▼           ▼     ▼                ▼     ▼
┌───────────────────────────────────────────────────────┐
│          Programs (Feeding, DRRM, Brigada)           │
└───────────────────────────────────────────────────────┘
```

Each bounded context owns its **aggregate roots** (e.g., `LessonPlan`, `StudentEnrollment`, `SchoolForm`). Cross‑domain relationships are expressed via foreign keys that are always tenant‑scoped.

---

## 3️⃣ Backend Folder Structure

```text
src/
├─ api/                     # FastAPI routers (HTTP + WS)
│   ├─ v1/
│   │   ├─ identity.py
│   │   ├─ students.py
│   │   ├─ lessons.py
│   │   ├─ assessments.py
│   │   ├─ gradebook.py
│   │   ├─ forms.py
│   │   └─ communication.py
│   └─ ws/
│       └─ notifications.py
├─ core/                    # Cross‑cutting utilities
│   ├─ config.py
│   ├─ logger.py
│   ├─ security/
│   │   ├─ auth.py
│   │   └─ rbac.py
│   └─ di.py                # Dependency‑Injection container
├─ domains/
│   ├─ identity/            # Users, roles, permissions
│   ├─ student/             # Students, enrollments, guardians
│   ├─ lesson/              # Lesson plans, versions, approvals
│   ├─ assessment/          # Quizzes, exams, rubrics
│   ├─ gradebook/           # Scores, computed grades, report cards
│   ├─ forms/               # DepEd school forms (SF1‑SF10)
│   ├─ communication/       # Parent messages, notifications
│   └─ reporting/           # RPMS, compliance reports
├─ infrastructure/
│   ├─ db/
│   │   ├─ models/          # SQLAlchemy 2.0 models mirroring DDL
│   │   ├─ session.py
│   │   └─ migrations/      # Alembic migration scripts
│   ├─ cache/               # Redis client
│   ├─ storage/              # S3 / Supabase client
│   ├─ message_queue/        # Celery app + task modules
│   └─ vector_db/            # pgvector repository
├─ services/
│   ├─ ai/                  # AI agents and LLM providers
│   ├─ workflow/             # Generic workflow engine
│   └─ analytics/           # Prometheus metrics helpers
├─ schemas/                # Pydantic request/response models
├─ tasks/                   # Celery/Dramatiq entry points
├─ events/                  # Event publisher & handlers
├─ integrations/            # External API wrappers (OpenAI, OCR, etc.)
├─ tests/                   # Unit, integration, and e2e tests
├─ scripts/                 # Helper scripts (bootstrap, etc.)
└─ main.py                  # FastAPI app creation and router inclusion
```

The `domains` layer never imports from `infrastructure` or `api`. All communication flows inward through the DI container (`core/di.py`).

---

## 4️⃣ Core Entities (mapped to the existing SQL)

| Domain | Table | Main Entity (SQLAlchemy model) |
|-------|-------|------------------------------|
| **Identity** | `users`, `roles`, `user_role_assignments` | `User`, `Role`, `UserRoleAssignment` |
| **Student** | `students`, `student_enrollments`, `guardians` | `Student`, `StudentEnrollment`, `Guardian` |
| **Lesson** | `lesson_plans`, `lesson_versions`, `lesson_approvals` | `LessonPlan`, `LessonVersion`, `LessonApproval` |
| **Assessment** | `assessment.assessments`, `assessment_items` | `Assessment`, `AssessmentItem` |
| **Gradebook** | `computed_grades`, `student_scores` | `ComputedGrade`, `StudentScore` |
| **Forms** | `school_forms`, `school_form_versions` | `SchoolForm`, `FormVersion` |
| **Audit** | `audit_logs` | `AuditLog` (append‑only) |

All entities include `tenant_id`, timestamps (`created_at`, `updated_at`), a nullable `deleted_at` for soft‑delete, and a flexible `metadata` JSONB column.

---

## 5️⃣ Sequence Diagrams (key workflows)

### 5.1 Lesson‑Plan Creation & AI Draft

```
Teacher → POST /api/v1/lessons
FastAPI → LessonService.create_plan()
LessonService → LessonRepository.add()
DB trigger → INSERT LessonVersion (v1)
FastAPI ← 201 Created (plan ID)

--- AI Generation ----------------------------------------------------
Teacher → POST /api/v1/lessons/{id}/ai-generate
FastAPI → AIService.run_agent('lesson', prompt)
AIService → AgentRegistry.get('lesson')
Agent → OpenAI completion()
Agent → returns JSON (objectives, procedure, activities)
AIService → persist AIOutput, link to LessonPlan
AIService → LessonService.apply_ai_output()
LessonService → creates new LessonVersion (v2)
FastAPI ← 200 OK (new version)
```

### 5.2 Grade Computation Batch

```
Celery Beat → compute_grades(school_year, period)
Task → GradebookService.compute_for_period()
Service → SELECT raw scores → CALL pg function gradebook.compute_grade()
Service → INSERT/UPDATE ComputedGrade (status=approved)
EventBus → publish GradeComputed
ReportCardService (handler) → creates ReportCard if needed
NotificationService → push to teacher/parents
```

### 5.3 SF2 (Attendance Form) Generation

```
Teacher → POST daily attendance → AttendanceService.record()
DB → attendance_records INSERT

--- End of Quarter ----------------------------------------------------
Scheduler → generate_sf2(school, quarter)
FormService → READ attendance (partitioned by school_year)
FormService → VALIDATE via FormValidationEngine
FormService → INSERT SchoolForm (status='draft')
FormService → CREATE FormVersion (snapshot)
FormExportTask → PDF generation → school_form_exports INSERT
FormService → status → 'approved'
EventBus → FormGenerated → AuditLog entry
```

### 5.4 AI‑Driven Risk Assessment

```
Scheduler → RiskService.evaluate_all()
RiskService → SELECT recent attendance & grades
RiskService → AIService.run_agent('risk', payload)
AIService → OpenAI → returns risk_score + recommendation
RiskService → INSERT risk_assessment, create InterventionCase
EventBus → publish InterventionCreated
NotificationService → send email/SMS to teacher & parents
```

---

## 6️⃣ API Architecture (REST + WebSocket)

| Resource | Method | Path | Description | Required Role |
|----------|--------|------|-------------|---------------|
| **Auth** | POST | `/api/v1/auth/login` | Returns JWT + Refresh | Public |
| | POST | `/api/v1/auth/refresh` | Refresh token | Authenticated |
| **Users** | GET | `/api/v1/users/me` | Profile | Any auth |
| | PATCH | `/api/v1/users/{id}` | Update | Self / Admin |
| **Students** | GET | `/api/v1/students` | List (filters) | Teacher / Admin |
| | POST | `/api/v1/students` | Enroll | Admin |
| **LessonPlans** | POST | `/api/v1/lessons` | Create draft | Teacher |
| | PATCH | `/api/v1/lessons/{id}` | Update (new version) | Owner / Admin |
| | POST | `/api/v1/lessons/{id}/approve` | Approve | Principal |
| **Assessments** | POST | `/api/v1/assessments` | Create quiz | Teacher |
| **Grades** | GET | `/api/v1/grades` | Query grades | Teacher / Parent |
| | POST (internal) | `/api/v1/grades/compute` | Trigger batch | System |
| **Forms** | POST | `/api/v1/forms/{code}` | Create form instance | Teacher |
| | GET | `/api/v1/forms/{id}/export` | Download PDF/Excel | Owner / Admin |
| **Communication** | POST | `/api/v1/notifications` | Send parent message | Teacher |
| **AI Agents** | POST | `/api/v1/ai/agents/{name}/run` | Execute AI task | Authenticated |
| **WebSocket** | `wss://.../ws/notifications` | Live notifications | Authenticated (JWT) |

All endpoints are versioned (`/api/v1/`), documented with OpenAPI, and support pagination, filtering, and sorting.

---

## 7️⃣ Event‑Driven Architecture

```
[Domain Services] ──► publish(event) ──► [Event Bus (Kafka/Redis Streams)]
        ▲                                   ▲
        │                                   │
   consumes                           consumes
        │                                   │
[Notification Service]        [Audit Logger]   [Report Service] …
```

**Core events (topic → payload)**

| Topic | Payload | Producer | Consumers |
|-------|---------|----------|-----------|
| `student.enrolled` | `{student_id, school_year_id, tenant_id}` | EnrollmentService | Analytics, Notification |
| `lesson.plan.approved` | `{plan_id, version_id, tenant_id}` | LessonWorkflow | Notification, Audit |
| `grade.computed` | `{grade_id, period_id, tenant_id}` | GradeComputationTask | ReportCardService, Analytics |
| `form.generated` | `{form_id, version, tenant_id}` | FormEngine | Audit, DepedIntegration |
| `ai.run.completed` | `{run_id, agent, cost, output_id}` | AIService | LessonService, AssessmentService |
| `intervention.created` | `{case_id, student_id}` | RiskService | Communication, Audit |

Events are JSON‑validated with Pydantic and stored in an **event store** table for replayability.

---

## 8️⃣ AI Agent Architecture

```
Agent Registry (DI)
   │
   ├─ LessonAgent
   ├─ AssessmentAgent
   ├─ GradebookAgent
   ├─ FormsAgent
   └─ RiskAgent
```

Each agent implements `run(prompt, context) → AIOutput`. Agents have:
* **Memory** – Redis cache of recent runs.
* **Tool access** – Search, calculation, lookup, etc.
* **Prompt versioning** – Stored in `ai.prompts`.

`AIOutput` rows (`ai.ai_outputs`) store the raw JSON, token usage, cost, and a foreign key back to the domain object (e.g., `lesson_plan.ai_output_id`).

---

## 9️⃣ Generic Workflow Engine (State Machine)

```python
class WorkflowEngine:
    def __init__(self, transitions: dict[State, dict[Event, State]]):
        self.transitions = transitions

    def next_state(self, cur: State, ev: Event) -> State:
        try:
            return self.transitions[cur][ev]
        except KeyError:
            raise ValueError(f"Invalid transition {cur}->{ev}")
```

Each bounded context supplies its own transition map (Lesson, Form, Gradebook). State changes are persisted and an event is emitted (`lesson.plan.approved`, …).

---

## 🔟 Security Architecture

| Layer | Implementation |
|-------|----------------|
| **Auth** | JWT (15 min) + HttpOnly refresh token (7 days) signed with RSA‑256 |
| **RBAC** | Roles (`teacher`, `principal`, `deped_admin`) ↔ Permissions (`lesson.create`, `grade.compute`) |
| **Multi‑tenant isolation** | `tenant_id` column + **Row‑Level Security** policies (see `14‑audit‑security.sql`) |
| **Transport** | TLS‑1.3 everywhere; optional mTLS for internal traffic |
| **Data‑at‑Rest** | PostgreSQL TDE / disk encryption; S3/Supabase with SSE‑S3 |
| **Secrets** | Docker secrets ↔ HashiCorp Vault, loaded via `core.config` |
| **Rate limiting** | `slowapi` middleware (per‑IP & per‑user token bucket) |
| **Audit** | Immutable `audit_logs`; only `app.bypass_rls=true` can INSERT |
| **Password hashing** | Argon2id (`passlib`) |
| **Session revocation** | JWT `jti` blacklist table checked on each request |
| **Compliance** | Export / delete endpoints for data‑subject requests (GDPR‑style) |

---

## 1️⃣1️⃣ Performance & Scalability Strategy

| Concern | Current | Next Steps |
|---------|---------|------------|
| **Indexes** | All FK + functional indexes; composite ones added for `computed_grades` & `school_forms`. | Add covering indexes for frequent reporting queries. |
| **Partitioning** | Planned LIST/BRIN partitions for `attendance_records` & `audit_logs`. | Automate partition creation per `school_year_id`. |
| **Caching** | Redis for sessions, short‑lived data. | Cache static reference data (`subjects`, `melcs`, `deped_config`). |
| **Read Replicas** | Single primary DB. | Deploy streaming replication; route read‑only APIs to replicas. |
| **Connection Pooling** | `asyncpg` pool (2 × CPU). | Tune pool size; set statement timeout. |
| **Bulk Loads** | INSERT per row. | Use PostgreSQL `COPY` for daily attendance imports (~200 M rows/yr). |
| **Materialized Views** | `attendance_summaries`, `gradebook` roll‑ups. | Refresh nightly with `pg_cron`; add `CONCURRENTLY` refresh. |
| **AI Cost Monitoring** | `ai_outputs.cost_cents`. | Dashboard per tenant; auto‑alert on budget breach. |

---

## 1️⃣2️⃣ Background Processing & Queue Design (Celery example)

```python
# infrastructure/message_queue/celery_app.py
celery = Celery(
    "teacheros",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
    include=[
        "tasks.grade_compute",
        "tasks.form_generate",
        "tasks.ai_generation",
        "tasks.ocr_processing",
    ],
)
```

**Typical tasks**
* `grade_compute.compute_grades(school_year, period)`
* `form_generate.generate_sf2(school_id, quarter)`
* `ai_generation.run_agent(agent_name, payload)`
* `ocr_processing.process_upload(file_id)`

All tasks publish an event on success and have exponential back‑off retries.

---

## 1️⃣3️⃣ Observability Stack

| Component | Tool | What it captures |
|-----------|------|-----------------|
| **Logging** | `structlog` + `loguru` | JSON logs (`request_id`, `tenant_id`, `user_id`). |
| **Metrics** | `prometheus_fastapi_instrumentator` | HTTP latency, error counters, queue depth, AI token usage. |
| **Tracing** | OpenTelemetry (`opentelemetry-instrumentation-fastapi`) | End‑to‑end traces across API → Service → DB → Celery. |
| **Dashboards** | Grafana (import ready dashboards) | SLA per tenant, AI spend, queue health. |
| **Alerting** | Prometheus Alertmanager → Slack/Email | `celery_queue_length > 10k`, `api_5xx_rate > 0.5%`, `cpu_usage > 80%`. |

All metrics are **namespaced per tenant** (e.g., `teacheros_api_request_seconds{tenant="school-123"}`).

---

## 1️⃣4️⃣ Testing Strategy

| Type | Scope | Tools |
|------|-------|-------|
| **Unit** | Domain services, repos, utils | `pytest`, `pytest‑asyncio`, `unittest.mock` |
| **Integration** | FastAPI + DB (Alembic migrations) | `httpx.AsyncClient`, `pytest‑postgresql` fixture |
| **Contract** | OpenAPI spec validation | `schemathesis` |
| **E2E** | Full flow (lesson → AI → approval) | `playwright` or `locust` |
| **Security** | Static analysis, OWASP ZAP | `bandit`, `snyk`, `zap-baseline.py` |
| **Performance** | Load tests for grade/computation, SF2 generation | `pgbench`, custom async scripts |
| **CI** | All above on PRs; gate on ≥ 80 % coverage, 0 critical findings. |

---

## 1️⃣5️⃣ DevOps / Deployment Architecture

### MVP – Docker‑Compose

```yaml
version: "3.9"
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes: ["db_data:/var/lib/postgresql/data"]
  redis:
    image: redis:7-alpine
  api:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    depends_on: [db, redis]
    ports: ["8000:8000"]
    env_file: .env
  worker:
    build: .
    command: celery -A infrastructure.message_queue.celery_app worker -Q default
    depends_on: [db, redis]
  beat:
    build: .
    command: celery -A infrastructure.message_queue.celery_app beat
    depends_on: [db, redis]
volumes:
  db_data:
```

### Production – Kubernetes (Helm)

* **PostgreSQL** (Patroni HA) + read‑replicas.
* **Redis** (cluster mode) for cache & Celery broker.
* **FastAPI Deployment** with HPA (CPU‑based).
* **Celery Workers** as separate Deployments, isolated by queue.
* **Ingress** (NGINX/Traefik) with TLS (Let’s Encrypt).
* **Prometheus‑Operator** for metrics scrape; **Grafana** for dashboards.
* **Argo CD** for GitOps – every commit triggers a Helm rollout.
* **Database migrations** run as an init‑container (`alembic upgrade head`).

---

## 1️⃣6️⃣ FastAPI Code Example (router + DI)

```python
# src/api/v1/lessons.py
from fastapi import APIRouter, Depends, HTTPException, status
from core.security import get_current_user, require_permission
from schemas.lesson import LessonCreate, LessonResponse
from services.lesson import LessonService
from core.di import get

router = APIRouter(prefix="/lessons", tags=["Lesson Plans"])

@router.post("/", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    payload: LessonCreate,
    user=Depends(get_current_user),
    service: LessonService = Depends(get(LessonService)),
):
    require_permission(user, "lesson.create")
    return await service.create_plan(payload, created_by=user.id)

@router.post("/{plan_id}/ai-generate", response_model=LessonResponse)
async def ai_generate(
    plan_id: str,
    prompt: str,
    user=Depends(get_current_user),
    service: LessonService = Depends(get(LessonService)),
):
    require_permission(user, "lesson.ai_generate")
    return await service.apply_ai_output(plan_id, prompt, user_id=user.id)
```

Dependencies are resolved from the DI container (`core/di.py`).

---

## 1️⃣7️⃣ Repository Pattern Example (SQLAlchemy 2.0)

```python
# infrastructure/db/models/lesson.py
class LessonPlanModel(Base):
    __tablename__ = "lesson_plans"
    __table_args__ = {"schema": "academic"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("academic.subjects.id"))
    teacher_user_id = Column(UUID(as_uuid=True), ForeignKey("core.users.id"))
    status = Column(Enum(LessonStatus), default=LessonStatus.DRAFT)
    current_version_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

```python
# domains/lesson/repos/lesson_repo.py
class LessonRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, entity: LessonPlanModel) -> LessonPlanModel:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get(self, plan_id: UUID) -> LessonPlanModel | None:
        return await self.session.get(LessonPlanModel, plan_id)

    async def list_by_teacher(self, teacher_id: UUID, skip: int = 0, limit: int = 20):
        stmt = (
            select(LessonPlanModel)
            .where(LessonPlanModel.teacher_user_id == teacher_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

---

## 1️⃣8️⃣ Service Layer / Use‑Case Example (LessonService)

```python
# services/lesson.py
from domains.lesson.entities.lesson_plan import LessonPlan
from domains.lesson.repos.lesson_repo import LessonRepository
from infrastructure.ai.agent_registry import AgentRegistry
from core.di import inject

class LessonService:
    @inject
    def __init__(self, repo: LessonRepository, agents: AgentRegistry):
        self.repo = repo
        self.agents = agents

    async def create_plan(self, dto: LessonCreateDTO, created_by: UUID) -> LessonResponseDTO:
        plan = LessonPlan(
            id=uuid4(),
            tenant_id=dto.tenant_id,
            subject_id=dto.subject_id,
            grade_level=dto.grade_level,
            teacher_user_id=created_by,
            status=LessonStatus.DRAFT,
        )
        await self.repo.add(plan.to_model())
        return LessonResponseDTO.from_entity(plan)

    async def apply_ai_output(self, plan_id: UUID, prompt: str, user_id: UUID):
        plan = await self.repo.get(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Lesson plan not found")
        agent = self.agents.get("lesson")
        ai_out = await agent.run(prompt, tenant_id=plan.tenant_id)
        plan.ai_output_id = ai_out.id
        # create a new immutable version (v+1)
        new_version = await self.repo.session.execute(
            insert(LessonVersionModel)
            .values(
                lesson_plan_id=plan_id,
                version_number=plan.current_version_id + 1,
                objectives=ai_out.payload["objectives"],
                procedure=ai_out.payload["procedure"],
                created_by=user_id,
            )
            .returning(LessonVersionModel)
        )
        plan.current_version_id = new_version.fetchone().id
        await self.repo.session.flush()
        # publish event
        from events.publisher import publish
        await publish("lesson.plan.ai_completed", {"plan_id": plan_id, "version_id": plan.current_version_id})
        return LessonResponseDTO.from_model(plan)
```

All domain rules (owner checks, tenant verification) live here before persisting.

---

## 1️⃣9️⃣ Dependency Injection (punq)

```python
# core/di.py
from punq import Container
from infrastructure.db.session import async_session_factory
from infrastructure.message_queue.celery_app import celery
from services.lesson import LessonService
from domains.lesson.repos.lesson_repo import LessonRepository
from infrastructure.ai.agent_registry import AgentRegistry

container = Container()
container.register_factory(AsyncSession, async_session_factory)
container.register_factory(LessonRepository, lambda: LessonRepository(container.resolve(AsyncSession)))
container.register_factory(AgentRegistry, lambda: AgentRegistry(celery))
container.register(LessonService, LessonService)

def get(dep):
    """FastAPI dependency helper"""
    return container.resolve(dep)
```

FastAPI endpoints import `get` and request the concrete service they need.

---

## 2️⃣0️⃣ Scalability & Future‑Growth Recommendations

| Future Need | How to Extend |
|-------------|----------------|
| **Division / Regional Offices** | Add `division_id`/`region_id` to `organizations`; extend RLS policies (`is_region_admin`). |
| **Self‑hosted LLMs** | Plug a local Ollama service into the `AIProvider` abstraction; no domain changes. |
| **Multi‑Region Deployments** | Separate PostgreSQL clusters per region; use **Citus** for distributed queries. |
| **Event Sourcing** | Replace simple Event Bus with Kafka Streams + persistent event store for replay & audit. |
| **Full‑Text Search Upgrade** | Migrate to **OpenSearch** for cross‑tenant search and relevance tuning. |
| **Realtime Collaboration** | Introduce **Y‑js** CRDT layer on top of WebSockets for simultaneous lesson editing. |
| **Feature Flags** | Store flags in `core.deped_config` (or a dedicated `feature_flags` table) and evaluate per tenant. |
| **Zero‑Downtime Migrations** | Use `pg_repack` for large tables; blue‑green deployments for API services. |
| **Data Warehouse** | Periodic ETL to Snowflake/BigQuery for analytics and training AI models. |
| **Compliance & Integrity** | Add a Merkle‑tree hash chain for `audit_logs` to prove immutability. |

---

*This file is intended to be version‑controlled alongside the SQL schema.  Add it to the repository (e.g., commit `ARCHITECTURE.md`) and reference it from the project README.*
