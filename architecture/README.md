# TeacherOS — Database Architecture (v1.0)

> Production-ready, multi-tenant, AI-native PostgreSQL schema for a nationwide Teacher Operating System aligned with DepEd (Philippines) workflows.

**Author:** Principal Database Architect & Enterprise Solutions Architect
**Target stack:** PostgreSQL 15+, Supabase-compatible, Row-Level Security
**Design capacity:** 1M+ students, 100K+ teachers, 5K+ schools, 200+ divisions
**Status:** v1.0 — Ready for implementation

---

## 0. Document Map

| File | Purpose |
|---|---|
| `README.md` (this) | High-level architecture, principles, bounded contexts, naming, scalability, operations |
| `01-auth-organization.sql` | Module 1: Auth, tenants, schools, roles |
| `02-student-information.sql` | Module 2: SIS, enrollments, attendance |
| `03-lesson-planning.sql` | Module 3: DLL, MELCs, lesson versions |
| `04-assessments.sql` | Module 4: Quizzes, items, rubrics, results |
| `05-gradebook.sql` | Module 5: Periods, categories, scores, report cards |
| `06-school-forms.sql` | Module 6: SF1/SF2/SF5/SF9/SF10 engine |
| `07-risk-intervention.sql` | Module 7: Risk scoring, cases, actions |
| `08-parent-communication.sql` | Module 8: Comms, templates, home visits |
| `09-reporting-compliance.sql` | Module 9: RPMS, reports, evidence |
| `10-school-programs.sql` | Module 10: Programs, budgets, activities |
| `11-documents.sql` | Module 11: Files, OCR, AI extraction |
| `12-ai-agents.sql` | Module 12: Agents, prompts, runs, outputs |
| `13-workflow-engine.sql` | Module 13: Workflows, steps, instances |
| `14-audit-security.sql` | Module 14: Audit, activity, notifications |
| `15-rls-policies.sql` | Consolidated RLS policies |
| `16-indexes.sql` | Consolidated index strategy |
| `17-materialized-views.sql` | Analytics layer |
| `18-events-triggers.sql` | Event-driven architecture |

---

## 1. High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              TeacherOS Platform                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│   │  Web App     │  │  Mobile PWA  │  │  Admin       │  │  Public API  │   │
│   │  (Teachers)  │  │  (Teachers)  │  │  Console     │  │  (Divisions) │   │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│          │                 │                 │                 │            │
│          └─────────────────┴────────┬────────┴─────────────────┘            │
│                                    │                                         │
│                          ┌─────────▼─────────┐                              │
│                          │   API Gateway     │  (Kong / Supabase Edge)       │
│                          │   + PostgREST     │                              │
│                          └─────────┬─────────┘                              │
│                                    │                                         │
│            ┌───────────────────────┼───────────────────────┐                │
│            │                       │                       │                │
│   ┌────────▼────────┐    ┌─────────▼─────────┐    ┌────────▼────────┐       │
│   │  Auth Service   │    │  Domain Services  │    │  AI Orchestrator│       │
│   │  (Supabase Auth)│    │  (Lesson, Grade,  │    │  (Agents, LLM)  │       │
│   │                 │    │  Forms, Comms)    │    │                 │       │
│   └────────┬────────┘    └─────────┬─────────┘    └────────┬────────┘       │
│            │                       │                       │                │
│            └───────────────────────┼───────────────────────┘                │
│                                    │                                         │
│                          ┌─────────▼─────────┐                              │
│                          │  Event Bus        │  (PostgreSQL LISTEN/NOTIFY    │
│                          │                   │   + Supabase Realtime +      │
│                          │                   │   pg_net for webhooks)       │
│                          └─────────┬─────────┘                              │
│                                    │                                         │
│        ┌───────────────────────────┼───────────────────────────┐            │
│        │                           │                           │            │
│   ┌────▼─────────┐         ┌───────▼────────┐         ┌───────▼────────┐   │
│   │ OLTP Schema  │         │ Analytics      │         │ Object Storage │   │
│   │ (PostgreSQL) │         │ (Read Replica  │         │ (S3 / Supabase │   │
│   │              │         │  + Warehouse)  │         │  Storage)      │   │
│   │ • RLS        │         │                │         │                │   │
│   │ • Multi-     │         │ • Materialized │         │ • Documents    │   │
│   │   tenant     │         │   views        │         │ • Avatars      │   │
│   │ • Versioning │         │ • Star schema  │         │ • Backups      │   │
│   │ • Audit      │         │ • pg_cron ETL  │         │                │   │
│   └──────────────┘         └────────────────┘         └────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Design Principles (Non-Negotiable)

### 2.1 Multi-Tenant Strategy — **Shared Schema with Discriminator + RLS**

**Chosen model:** Shared database, shared schema. Every domain table carries a `tenant_id` (which is a `school_id` for school-scoped data, or an `organization_id` for org-level data). Row-Level Security enforces isolation.

**Why:**
- Lowest operational cost (one DB cluster, one connection pool)
- Easiest cross-tenant analytics (DepEd-wide reporting, division rollups)
- Supabase-native (RLS is the canonical pattern)
- No application-level tenant filtering bugs possible

**Rejected alternatives:**
- *Schema-per-tenant*: Too many schemas to manage at 5K+ schools; painful migrations; doesn't scale to millions of tables.
- *Database-per-tenant*: High cost, slow cross-tenant queries, disaster recovery complexity.

### 2.2 Workflow-First, Screen-Second

The schema mirrors **business workflows**, not UI screens. Each workflow has:
- A canonical state machine in `workflow_statuses`
- A `workflow_instance` row per execution
- A `workflow_step` progression log
- A set of domain tables the workflow writes to

This means the same data model survives UI redesigns, mobile apps, and API surface changes.

### 2.3 AI-Native (Not AI-Bolted-On)

AI is a first-class citizen. Every AI-generated artifact:
- Has provenance (`ai_output_id` linking to the prompt + model + run)
- Has a human-review state (`draft`, `pending_review`, `approved`, `rejected`, `edited`)
- Can be regenerated without losing history (immutable `ai_outputs` + versioned `prompt_versions`)
- Tracks cost (tokens, model, latency) for billing and FinOps

### 2.4 Soft Deletes + Audit By Default

Nothing is `DELETE`d from domain tables. Every table has:
- `deleted_at TIMESTAMPTZ NULL` — tombstone for soft delete
- `created_at`, `updated_at` — automatic timestamps
- `created_by`, `updated_by` — actor reference

Sensitive mutations go through `audit_logs` (immutable append-only, no UPDATE/DELETE permission).

### 2.5 Versioning Where It Matters

Tables that capture human work products (lesson plans, report cards, school forms, rubrics) get explicit version tables. This enables:
- Diff comparison
- Rollback
- Compliance "show me what was submitted on March 15"
- "Regenerate with this older prompt"

### 2.6 UUIDs Everywhere, No Surrogate INTs

Every primary key is `UUID` (`gen_random_uuid()` or `uuidv7()` for time-ordered keys). Why:
- Safe to expose in URLs (no enumeration attacks)
- Merge-friendly across environments
- Distributed-system friendly
- No "what ID will the next insert get" race conditions

### 2.7 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Tables | `snake_case`, **plural** nouns | `students`, `lesson_plans` |
| Columns | `snake_case` | `first_name`, `school_id` |
| PK | `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` | `id` |
| FK | `<referenced_table_singular>_id` | `school_id`, `student_id` |
| Boolean | `is_*` or `has_*` prefix | `is_active`, `has_graduated` |
| Timestamps | `*_at` suffix | `created_at`, `deleted_at` |
| Audit actor | `*_by` suffix | `created_by`, `approved_by` |
| Enum | PostgreSQL `CREATE TYPE ... AS ENUM` | `student_status` |
| JSONB | `*_data` or `*_meta` suffix | `metadata JSONB` |
| Indexes | `idx_<table>_<columns>` | `idx_students_school_id_lrn` |
| Unique | `uq_<table>_<columns>` | `uq_users_email` |
| RLS policy | `rls_<table>_<action>` | `rls_lesson_plans_select_teacher` |

### 2.8 Schema Layout

```
schemas/
├── core          — Identity, tenants, users, roles
├── sis           — Student information
├── academic      — Subjects, MELCs, lessons, assessments, grades
├── forms         — DepEd school forms
├── intervention  — Risk, cases
├── communication — Parent comms
├── compliance    — Reports, RPMS, evidence
├── programs      — School programs
├── documents     — Document management
├── ai            — AI agents, prompts, outputs
├── workflow      — Workflow engine
├── audit         — Audit & security
└── analytics     — Materialized views, reporting tables (read-mostly)
```

All app code references tables as `core.users`, `sis.students`, etc. This prevents table-name collisions and makes ownership clear.

---

## 3. Domain-Driven Design — Bounded Contexts

```
                    ┌─────────────────────────────────────────────┐
                    │         Identity & Tenancy Context          │
                    │  (orgs, schools, users, roles, RLS context) │
                    └────────────────┬────────────────────────────┘
                                     │
       ┌─────────────┬───────────────┼───────────────┬─────────────┐
       │             │               │               │             │
┌──────▼──────┐ ┌────▼─────┐ ┌───────▼────────┐ ┌─────▼──────┐ ┌───▼────────┐
│  Academic   │ │   SIS    │ │  DepEd Forms   │ │ Interven-  │ │ Reporting  │
│  Context    │ │ Context  │ │    Context     │ │ tion Ctx   │ │ Context    │
│             │ │          │ │                │ │            │ │            │
│ • Subjects  │ │ • Stu-   │ │ • School Forms │ │ • Risk     │ │ • RPMS     │
│ • MELCs     │ │   dents  │ │ • Submissions  │ │   scoring  │ │ • Reports  │
│ • Lessons   │ │ • Sec-   │ │ • Validations  │ │ • Cases    │ │ • Evidence │
│ • Assess-   │ │   tions  │ │ • Exports      │ │ • Actions  │ │ • Submis-  │
│   ments     │ │ • Atten- │ │                │ │ • Notes    │ │   sions    │
│ • Grades    │ │   dance  │ │                │ │            │ │            │
│ • Report    │ │ • Guard- │ │                │ │            │ │            │
│   cards     │ │   ians   │ │                │ │            │ │            │
└──────┬──────┘ └────┬─────┘ └───────┬────────┘ └─────┬──────┘ └───┬────────┘
       │             │              │                 │            │
       └─────────────┴──────────────┼─────────────────┴────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  AI Agent Context │
                          │  (cross-cutting)  │
                          └─────────┬─────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  Workflow Context │
                          │  (orchestration)  │
                          └─────────┬─────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  Audit & Observ.  │
                          │  (cross-cutting)  │
                          └───────────────────┘
```

**Bounded Context Rules:**
- Each context owns its data; cross-context references use IDs only (no foreign keys across schemas).
- AI Agent Context consumes any other context via events and writes back to it via the workflow engine.
- Audit context is read-only consumers of every other context (writes via triggers, never direct).

---

## 4. Cross-Cutting Concerns (Present in Every Table)

### 4.1 Standard Columns

```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
tenant_id       UUID NOT NULL,                       -- for RLS
created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
created_by      UUID REFERENCES core.users(id),
updated_by      UUID REFERENCES core.users(id),
deleted_at      TIMESTAMPTZ NULL,                    -- soft delete
metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
```

The `updated_at` trigger is centralized:

```sql
CREATE OR REPLACE FUNCTION core.tg_set_updated_at() RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 4.2 Standard Trigger

Every domain table gets:
```sql
CREATE TRIGGER tg_set_updated_at BEFORE UPDATE ON <table>
  FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
```

### 4.3 Tenant Discriminator

- `tenant_id` is the **school_id** for school-scoped data (lesson plans, grades, attendance, lesson plans, school forms).
- `tenant_id` is the **organization_id** for org-scoped data (programs, district reports, DRRM).
- For data shared across the entire deployment (DepEd-wide reference data: MELCs, SF templates, public DepEd school list), `tenant_id` is NULL and RLS allows public read.

The session variable `app.current_tenant_id` (set on every connection from the API) drives RLS.

---

## 5. Multi-Tenant + RLS Strategy

### 5.1 Session Variables

The application sets these on every connection:
- `app.current_user_id` — authenticated user UUID
- `app.current_tenant_id` — current school_id (or org_id)
- `app.current_role` — role code (teacher, principal, etc.)
- `app.bypass_rls` — `true` only for system jobs (cron, migrations, support)

### 5.2 RLS Helper Functions

```sql
-- Get current tenant safely
CREATE FUNCTION core.current_tenant_id() RETURNS UUID
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.current_tenant_id', true), '')::UUID;
$$;

-- Get current user
CREATE FUNCTION core.current_user_id() RETURNS UUID
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.current_user_id', true), '')::UUID;
$$;

-- Is current user a principal/admin of current tenant?
CREATE FUNCTION core.is_tenant_admin() RETURNS BOOLEAN
LANGUAGE sql STABLE AS $$
  SELECT EXISTS (
    SELECT 1 FROM core.user_role_assignments
    WHERE user_id = core.current_user_id()
      AND tenant_id = core.current_tenant_id()
      AND role_id IN (SELECT id FROM core.roles
                      WHERE code IN ('principal', 'head', 'admin', 'division_staff'))
      AND deleted_at IS NULL
  );
$$;
```

### 5.3 RLS Pattern Per Table (Example)

```sql
ALTER TABLE academic.lesson_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic.lesson_plans FORCE ROW LEVEL SECURITY;

-- Read: any user in the same tenant
CREATE POLICY rls_lesson_plans_select ON academic.lesson_plans
  FOR SELECT USING (
    tenant_id = core.current_tenant_id()
    AND deleted_at IS NULL
  );

-- Insert: teachers and above
CREATE POLICY rls_lesson_plans_insert ON academic.lesson_plans
  FOR INSERT WITH CHECK (
    tenant_id = core.current_tenant_id()
    AND core.current_user_id() IS NOT NULL
  );

-- Update: only the author or a principal
CREATE POLICY rls_lesson_plans_update ON academic.lesson_plans
  FOR UPDATE USING (
    tenant_id = core.current_tenant_id()
    AND (created_by = core.current_user_id() OR core.is_tenant_admin())
  );

-- Delete: principal only, soft-delete only
CREATE POLICY rls_lesson_plans_delete ON academic.lesson_plans
  FOR DELETE USING (core.is_tenant_admin());
```

### 5.4 Cross-Tenant Data (Org-Level, Division-Level)

Some data lives at the organization or division level (e.g., division-wide reports, district programs). For these, `tenant_id` is the **organization_id** and the RLS checks a user's membership in that org:

```sql
CREATE POLICY rls_programs_select ON programs.programs
  FOR SELECT USING (
    tenant_id IN (
      SELECT organization_id FROM core.organization_members
      WHERE user_id = core.current_user_id() AND deleted_at IS NULL
    )
  );
```

### 5.5 DepEd-Wide Reference Data (No Tenant)

For MELCs, SF templates, and the public DepEd school list, `tenant_id` is NULL. RLS policy is:

```sql
CREATE POLICY rls_melcs_select_public ON academic.melcs
  FOR SELECT USING (tenant_id IS NULL);  -- reference data visible to all
```

Reference data is seeded by DepEd admins via a separate `app.bypass_rls = true` connection.

---

## 6. Event-Driven Architecture

### 6.1 Why Events

Several workflows are inherently cross-context:
- "AI agent generates lesson plan draft" → workflow notifies teacher → teacher edits → AI regenerates → ...
- "Risk score crosses threshold" → create intervention case → notify principal → log in compliance report
- "Student enrollment changes" → recompute class lists → invalidate cached grade summaries

Instead of a direct service-to-service call (which creates coupling and breakage), every domain event is published to an event log that other contexts subscribe to.

### 6.2 Event Log Table

```sql
CREATE TABLE audit.domain_events (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL,
  event_type      TEXT NOT NULL,           -- e.g., 'lesson_plan.submitted'
  event_version   INT  NOT NULL DEFAULT 1,
  aggregate_type  TEXT NOT NULL,           -- e.g., 'lesson_plan'
  aggregate_id    UUID NOT NULL,
  payload         JSONB NOT NULL,
  occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  produced_by     UUID,                    -- user or agent_run that caused it
  correlation_id  UUID,                    -- for tracing a multi-step workflow
  published_at    TIMESTAMPTZ,             -- when sent to subscribers
  retry_count     INT NOT NULL DEFAULT 0,
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'published', 'failed', 'dead_letter')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.3 Publishing Mechanism

A trigger on every domain table writes to `domain_events` on INSERT/UPDATE/DELETE:

```sql
CREATE FUNCTION audit.tg_emit_domain_event() RETURNS TRIGGER AS $$
DECLARE
  v_event_type TEXT;
  v_payload JSONB;
BEGIN
  v_event_type := TG_ARGV[0];
  v_payload := jsonb_build_object(
    'operation', TG_OP,
    'before', to_jsonb(OLD),
    'after',  to_jsonb(NEW)
  );
  INSERT INTO audit.domain_events
    (tenant_id, event_type, aggregate_type, aggregate_id, payload, produced_by)
  VALUES
    (NEW.tenant_id, v_event_type, TG_ARGV[1], NEW.id, v_payload,
     NULLIF(current_setting('app.current_user_id', true), '')::UUID);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

Per-table triggers look like:
```sql
CREATE TRIGGER tg_emit_lesson_plan_events
  AFTER INSERT OR UPDATE ON academic.lesson_plans
  FOR EACH ROW EXECUTE FUNCTION audit.tg_emit_domain_event('lesson_plan.changed', 'lesson_plan');
```

### 6.4 Subscribers (Workers)

Workers consume from `domain_events WHERE status = 'pending'` (using `FOR UPDATE SKIP LOCKED` for horizontal scaling) and run business logic. After successful processing, they mark the event `published`. On failure, they increment `retry_count` with exponential backoff; after N retries, the event moves to `dead_letter`.

In Supabase, the same pattern is implemented via `pg_net` calling Edge Functions, or via external workers polling the table.

---

## 7. Analytics Layer

### 7.1 Read Replica Strategy

PostgreSQL streaming replication provides a hot read replica. All `analytics.*` materialized views are refreshed ON the replica (via logical decoding into the replica's own schema), so heavy analytical queries never touch the OLTP primary.

### 7.2 Materialized Views (Key Examples)

See `17-materialized-views.sql` for full DDL. Highlights:

- `analytics.mv_student_performance_trend` — quarterly grade averages per student
- `analytics.mv_attendance_daily` — daily attendance by section
- `analytics.mv_teacher_productivity` — counts of lesson plans, assessments, grades per teacher
- `analytics.mv_school_compliance` — completeness scores for each DepEd form per school
- `analytics.mv_at_risk_students` — students with risk_score > threshold

All materialized views are refreshed by `pg_cron` on a schedule (e.g., nightly at 02:00) and incrementally when possible (via `REFRESH MATERIALIZED VIEW CONCURRENTLY`).

### 7.3 Star Schema for BI

A separate `analytics` schema holds denormalized fact/dimension tables for BI tools (Metabase, PowerBI, Superset). ETL via `pg_cron` jobs copy from OLTP into the star schema nightly.

---

## 8. Indexing Strategy

| Pattern | Index Type | Example |
|---|---|---|
| PK | `btree` (default with UUID) | `id` |
| FK columns | `btree` | `(tenant_id)`, `(school_id)` |
| Composite tenant + lookup | `btree` composite | `(tenant_id, school_id, lrn)` |
| Soft-delete filter | `btree` partial | `WHERE deleted_at IS NULL` |
| Time range | `btree` on `*_at` | `(school_id, created_at DESC)` |
| JSONB queries | `gin` | `metadata jsonb_path_ops` |
| Full text | `gin` | `to_tsvector('english', name)` |
| Unique constraints | `btree` unique | `UNIQUE (tenant_id, email)` |
| LRN (Student ID) | `btree` | `UNIQUE (tenant_id, lrn)` |

Key rules:
1. **Every FK is indexed** — enables CASCADE and JOIN performance.
2. **Every `(tenant_id, ...)` is a composite index** — RLS evaluates `tenant_id` on every query, so leading with it makes the index highly selective.
3. **All soft-deleted tables get a partial index** excluding `deleted_at IS NOT NULL` so production queries don't scan tombstones.
4. **JSONB only when truly schema-less** — when a structure is known, use real columns + computed generated columns.
5. **No over-indexing on writes** — measure before adding.

Full DDL in `16-indexes.sql`.

---

## 9. Scalability for 1M+ Students

| Concern | Strategy |
|---|---|
| Read throughput | Read replicas + PgBouncer connection pooling |
| Write throughput | Partitioning large tables by `tenant_id` (hash) or by `school_year_id` (range) |
| Storage growth | TimescaleDB or native PG partitioning for `attendance_records`, `audit_logs` (which are insert-only and time-series) |
| Connection storms | PgBouncer transaction pooling (1000s of clients → 100s of PG connections) |
| Cold start | Pre-warm materialized views after maintenance windows |
| Hot schools | `pg_advisory_lock` for per-school serialization of heavy writes (e.g., report card generation) |
| Cross-tenant analytics | Move to dedicated analytics cluster (logical replication) |
| Disaster recovery | PITR + cross-region read replica + S3 WAL archiving |

### Partitioning Examples

```sql
-- Partition attendance by school_year (range) + hash
CREATE TABLE sis.attendance_records (LIKE sis.attendance_records_template)
  PARTITION BY LIST (school_year_id);

-- Partition audit_logs by month (time-series)
CREATE TABLE audit.audit_logs (LIKE audit.audit_logs_template)
  PARTITION BY RANGE (created_at);
```

---

## 10. Backup & Disaster Recovery

| Concern | Policy |
|---|---|
| RPO (Recovery Point Objective) | ≤ 5 minutes (PITR + WAL streaming to S3) |
| RTO (Recovery Time Objective) | ≤ 30 minutes (hot standby + automated failover via Patroni) |
| Backups | Daily full (compressed) + continuous WAL archiving to S3 (cross-region) |
| Retention | 30 days point-in-time, 7 years for `audit_logs` (DepEd compliance) |
| Encryption | TLS in transit, AES-256 at rest (managed by cloud provider) |
| DR drill | Quarterly failover test to secondary region |
| Tenant data export | Self-service: any principal can request a full export of their school's data (GDPR-equivalent + DepEd right-to-data) |

### Recommended Setup

- **Primary region:** `ap-southeast-1` (Singapore, closest to PH with low latency)
- **DR region:** `ap-southeast-2` (Sydney) or `ap-northeast-1` (Tokyo)
- **Provider:** Supabase (managed) for v1, can self-host on RDS/Aurora or Citus for hyperscale
- **HA:** 1 primary + 1 sync standby + 1 async DR replica

---

## 11. Migration Strategy

### 11.1 Tooling

Use **sqitch**, **dbmate**, or **Flyway** for versioned, reviewable SQL migrations. Migrations live in `migrations/` with timestamped filenames: `2026-06-08-001-core-schema.sql`.

### 11.2 Pattern

1. **Backward-compatible migrations only.** Adding columns, tables, indexes is safe.
2. **Destructive changes (drop column, rename, type change) require a 3-phase deploy:**
   - Phase 1: Add new column, dual-write via trigger
   - Phase 2: Backfill data, switch app reads to new column
   - Phase 3: Drop old column
3. **All migrations are tested in CI** with `pg_regress` or a transactional test harness that spins up a fresh DB.
4. **Long migrations** (>10 min on production-sized data) use `pg_repack` or run in chunks with progress tracking.

### 11.3 Seed Data

- Reference data (MELCs, SF templates, DepEd school list) seeded via `seeds/` directory
- Run idempotently: every INSERT uses `ON CONFLICT DO NOTHING`
- Dev/staging seeds: small fixtures for tests
- Prod seeds: only DepEd reference data; never seed user data

---

## 12. Performance Optimizations (Summary)

| Optimization | Where |
|---|---|
| Partial indexes for soft-deleted rows | Every domain table |
| Composite leading with `tenant_id` | Every multi-tenant index |
| `pg_stat_statements` monitoring | Enabled by default |
| Statement timeouts | `SET statement_timeout = '30s'` per role |
| Connection pooling | PgBouncer transaction mode |
| Covering indexes for hot queries | Materialized view refresh, dashboard reads |
| `BRIN` indexes | For append-only time-series (`audit_logs`, `domain_events`) |
| `LIST`/`RANGE` partitioning | Large tables (attendance, audit, events) |
| `pg_cron` for heavy jobs | Materialized view refresh, exports, retention purges |
| `EXPLAIN ANALYZE` in CI | Every PR must not regress query plans on golden dataset |

---

## 13. Open Architectural Decisions (Recorded ADRs)

| ADR | Decision | Status |
|---|---|---|
| ADR-001 | Multi-tenancy via shared schema + RLS | ✅ Accepted |
| ADR-002 | UUID v4 (not v7) for v1; v7 migration planned | ✅ Accepted |
| ADR-003 | Event log table (not pure LISTEN/NOTIFY) for durability | ✅ Accepted |
| ADR-004 | JSONB for `metadata` only; structured columns preferred | ✅ Accepted |
| ADR-005 | Soft delete via `deleted_at` + partial index | ✅ Accepted |
| ADR-006 | Workflow engine as in-house schema (not Temporal/Camunda) | ✅ Accepted for v1; revisit at v3 |
| ADR-007 | `pg_cron` for jobs; no external scheduler | ✅ Accepted |
| ADR-008 | Supabase as primary hosting; portable to self-hosted PG | ✅ Accepted |

---

## 14. How to Read the SQL Files

Every SQL file in this architecture follows the same structure:

```sql
-- =============================================================
-- Module N: <name>
-- Depends on: core (auth/orgs/users)
-- Tables: <list>
-- =============================================================

SET search_path TO <schema>, core, public;

-- 1. ENUMs
CREATE TYPE ...;

-- 2. Tables
CREATE TABLE ...;
CREATE TRIGGER ...;
CREATE INDEX ...;

-- 3. Comments (table + column docstrings)
COMMENT ON TABLE ... IS '...';

-- 4. RLS (also collected centrally in 15-rls-policies.sql)
ALTER TABLE ... ENABLE ROW LEVEL SECURITY;
```

The companion `15-rls-policies.sql` consolidates all RLS so security audits are a single-file review. The `16-indexes.sql` does the same for index review. **Both are redundant by design** (RLS is also created in the module file) — the consolidated file is the source of truth for the security team; the module files keep related DDL together for engineers.

---

**Next file:** `01-auth-organization.sql` — Module 1 implementation.
