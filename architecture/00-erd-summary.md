# TeacherOS — Architecture Summary

> 📖 **Start with [`README.md`](./README.md)** for the complete architecture overview, design principles, bounded contexts, naming conventions, and operational strategies.

## File Map (What's in this folder)

| File | Purpose | Status |
|---|---|---|
| `README.md` | Complete architecture overview: design principles, bounded contexts, naming, RLS strategy, events, analytics, ops | ✅ |
| `00-erd-summary.md` | **This file** — Quick reference map | ✅ |
| `01-auth-organization.sql` | Module 1: Tenants, schools, users, roles, RLS helpers, 13 system roles seeded | ✅ |
| `02-student-information.sql` | Module 2: Students, enrollments, attendance, guardians, transfers | ✅ |
| `03-lesson-planning.sql` | Module 3: Subjects, MELCs, lesson plans with versioning, DLL, approvals | ✅ |
| `04-assessments.sql` | Module 4: Quizzes, items, rubrics, AI-grading, student responses | ✅ |
| `05-gradebook.sql` | Module 5: Quarterly grading, DepEd transmutation, report cards | ✅ |
| `06-school-forms.sql` | Module 6: SF1/SF2/SF5/SF9/SF10 engine with validation, lock-on-submit | ✅ |
| `07-risk-intervention.sql` | Module 7: Risk scoring, intervention cases, AI-suggested actions | ✅ |
| `08-parent-communication.sql` | Module 8: SMS/email, templates, home visits, parent conferences, SMS outbox | ✅ |
| `09-reporting-compliance.sql` | Module 9: RPMS, accomplishment reports, KPI metrics, evidence | ✅ |
| `10-school-programs.sql` | Module 10: Feeding, DRRM, Brigada, events, beneficiaries, budgets | ✅ |
| `11-14-ai-docs-workflow-audit.sql` | Modules 11-13: Documents, AI agents (Prompts, Runs, Outputs, Feedback), Workflow Engine | ✅ (consolidated) |
| `14-audit-security.sql` | Module 14: Immutable audit logs, activity feed, login history, notifications | ✅ |
| `15-17-rls-indexes-mv.sql` | Files 15-17: RLS review checklist, indexes, analytics layer (5 materialized views) | ✅ (consolidated) |
| `18-deployment-guide.sql` | File 18: Roles/grants, pg_cron schedules, health checks, DR runbook, DepEd compliance | ✅ |

> **Note on consolidation:** Files 11-13 share one SQL file because they are heavily interlinked (documents reference AI runs, workflows reference both documents and AI). Files 15-17 share another because RLS and indexes are inline in every module, and the consolidated file is the security review source of truth. The numbers in the filenames still match the original 14-module spec for traceability.

---

## At-a-Glance: What This Architecture Delivers

### 14 Bounded Contexts (Schemas)

| Schema | Purpose | Key Tables |
|---|---|---|
| `core` | Identity & tenancy | `organizations`, `schools`, `users`, `roles`, `user_role_assignments` |
| `sis` | Student information | `students`, `student_enrollments`, `attendance_records`, `guardians` |
| `academic` | Lesson planning | `subjects`, `melcs`, `lesson_plans`, `lesson_versions` |
| `assessment` | Tests & grading | `assessments`, `assessment_items`, `rubrics`, `assessment_results` |
| `gradebook` | Final grades | `student_scores`, `computed_grades`, `report_cards` |
| `forms` | DepEd forms | `school_forms`, `school_form_templates`, `school_form_validations` |
| `intervention` | At-risk students | `risk_assessments`, `intervention_cases`, `intervention_actions` |
| `comms` | Parent comms | `communications`, `communication_recipients`, `sms_outbox` |
| `compliance` | RPMS & reports | `reports`, `report_submissions`, `kpi_metrics` |
| `programs` | School programs | `programs`, `beneficiaries`, `program_budgets` |
| `documents` | Document mgmt | `documents`, `document_versions`, `extracted_content` |
| `ai` | AI agents | `ai_agents`, `agent_runs`, `ai_outputs`, `prompts`, `prompt_versions` |
| `workflow` | Workflow engine | `workflows`, `workflow_steps`, `workflow_instances` |
| `audit` | Audit & security | `audit_logs`, `notifications`, `login_history` |
| `analytics` | (read-mostly) | 5 materialized views |

### Cross-Cutting Concerns Built-In

- **UUID v4** primary keys everywhere (safe to expose, merge-friendly, distributed-safe)
- **`tenant_id`** discriminator on every domain table for RLS
- **Soft delete** via `deleted_at TIMESTAMPTZ` + partial indexes
- **Audit columns** (`created_at`, `updated_at`, `created_by`, `updated_by`) on every table
- **`metadata JSONB`** for schema-less extensions
- **PostgreSQL ENUMs** for stable domain types
- **Row-Level Security** enabled and FORCED on every domain table
- **Cascading FKs** where appropriate
- **Partial indexes** for `deleted_at IS NULL` filter (production query speed)
- **Generated columns** for derived values (e.g., `percentage` in grades)
- **Immutable audit logs** enforced by triggers

### DepEd-Specific Features

- DepEd 2020 MELC matrix schema (with `deped_version` for future matrix updates)
- DepEd K-12 transmutation table function (`gradebook.deped_transmute()`)
- DepEd rating labels (`Outstanding`, `Very Satisfactory`, etc.)
- SF1/SF2/SF5/SF9/SF10 form engine with versioned templates
- Lock-on-submit semantics for DepEd submissions
- RPMS indicators (Phase II COT, Phase III outcomes, plus factors)
- BRIGADA Eskwela, DRRM, SBFP (School-Based Feeding Program) schema
- 4Ps beneficiary tracking
- Indigenous Peoples (IP) tracking
- SPED, learner with disability tracking
- Modality tracking (face-to-face, modular, online, blended, homeschooling)

### AI-Native Features

- 12 specialized AI agent kinds (lesson drafter, form validator, grader, etc.)
- **Versioned prompt library** (like code versions)
- **Immutable `ai_outputs` table** with provenance, state, and regeneration tracking
- **Auto-supersede** of prior outputs when a new one is created (audit trail preserved)
- **Human-in-the-loop** with explicit `review_state` (`pending`, `in_review`, `approved`, `rejected`, `edited`)
- **Per-run cost tracking** (tokens, model, latency) for FinOps
- **AI feedback** with 1-5 ratings + free-text + edited-output capture
- **Domain events** via triggers for cross-context agent orchestration

### Production-Ready Operations

- **DR runbook** with RTO 30min / RPO 5min targets
- **Backup strategy**: Daily full + continuous WAL archiving to S3 (cross-region)
- **pg_cron schedules** for materialized view refresh, retention purge, reindex
- **Health check queries** for monitoring
- **Data migration strategy** with phase-by-phase plan from existing SIS systems
- **Compliance checklists** for RA 10173 (Data Privacy Act) and DepEd requirements

---

## Quick Stats

- **Schemas:** 15 (14 domain + analytics)
- **Tables:** ~90 (60+ domain tables, 20+ version/log tables, 5 materialized views)
- **Custom ENUMs:** ~50
- **RLS Policies:** 100+ (every domain table has read + write policies)
- **Indexes:** 300+ (including partial, GIN, BRIN, trigram)
- **Triggers:** 100+ (updated_at + domain event emission)
- **Helper Functions:** 30+ (DepEd transmutation, compute_grade, RLS helpers, etc.)
- **Materialized Views:** 5 (performance trend, attendance, teacher productivity, compliance, at-risk)
- **Lines of SQL:** ~12,000
