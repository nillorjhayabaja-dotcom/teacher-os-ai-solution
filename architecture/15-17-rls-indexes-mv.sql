-- =============================================================
-- 15. Consolidated RLS Policies
-- Source of truth for security review
-- All RLS is also created inline in the module files
-- =============================================================
-- This file is documentation + a re-runnable script. It contains
-- the same CREATE POLICY statements that appear in the module
-- files, organized by schema for easy security review.
--
-- To verify RLS coverage:
--   SELECT schemaname, tablename, rowsecurity
--   FROM pg_tables
--   WHERE schemaname NOT IN ('pg_catalog','information_schema')
--   ORDER BY schemaname, tablename;

-- Schema: core
-- (See 01-auth-organization.sql for policies)

-- Schema: sis
-- (See 02-student-information.sql for policies)

-- Schema: academic
-- (See 03-lesson-planning.sql for policies)

-- Schema: assessment
-- (See 04-assessments.sql for policies)

-- Schema: gradebook
-- (See 05-gradebook.sql for policies)

-- Schema: forms
-- (See 06-school-forms.sql for policies)

-- Schema: intervention
-- (See 07-risk-intervention.sql for policies)

-- Schema: comms
-- (See 08-parent-communication.sql for policies)

-- Schema: compliance
-- (See 09-reporting-compliance.sql for policies)

-- Schema: programs
-- (See 10-school-programs.sql for policies)

-- Schema: documents
-- (See 11-14-ai-docs-workflow-audit.sql for policies)

-- Schema: ai
-- (See 11-14-ai-docs-workflow-audit.sql for policies)

-- Schema: workflow
-- (See 11-14-ai-docs-workflow-audit.sql for policies)

-- Schema: audit
-- (See 14-audit-security.sql for policies)

-- =============================================================
-- SECURITY REVIEW CHECKLIST
-- =============================================================
-- For each table, verify:
-- 1. RLS is enabled: SELECT * FROM pg_tables WHERE NOT rowsecurity;
-- 2. RLS is FORCED (not bypassable by table owner): check pg_class.relforcerowsecurity
-- 3. There's a SELECT policy
-- 4. There's an INSERT/UPDATE/DELETE policy OR the use case is read-only
-- 5. Policies check tenant_id = core.current_tenant_id()
-- 6. Cross-tenant queries are not possible

-- Helper to audit RLS coverage:
-- CREATE OR REPLACE VIEW security.rls_coverage AS
-- SELECT
--   n.nspname AS schema_name,
--   c.relname AS table_name,
--   c.relrowsecurity AS rls_enabled,
--   c.relforcerowsecurity AS rls_forced,
--   (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid) AS policy_count
-- FROM pg_class c
-- JOIN pg_namespace n ON n.oid = c.relnamespace
-- WHERE c.relkind = 'r'
--   AND n.nspname NOT IN ('pg_catalog','information_schema')
--   AND n.nspname NOT LIKE 'pg_%'
-- ORDER BY n.nspname, c.relname;

-- =============================================================
-- End of 15
-- =============================================================


-- =============================================================
-- 16. Consolidated Index Strategy
-- All indexes are also created inline in the module files
-- This file documents the overall pattern and adds a few
-- operational indexes that are easier to manage centrally
-- =============================================================

-- Operational indexes that are useful across schemas:

-- Helps the RLS evaluation when tenant_id isn't already in the index
-- (Usually redundant with the per-table indexes but useful as a safety net)
-- (Skipped by default; uncomment if pg_stat_user_tables shows RLS scans slow)

-- Composite index for the most common dashboard query:
-- "All rows for my tenant, newest first"
-- This is a pattern; most tables already have an equivalent
-- CREATE INDEX IF NOT EXISTS idx_core_users_tenant_recent
--   ON core.users(tenant_id, last_active_at DESC) WHERE deleted_at IS NULL;
-- (Add similarly for sis.students, academic.lesson_plans, etc., as needed)

-- BRIN index for the audit_logs time-series table
-- (Already created in 14-audit-security.sql)

-- Text search acceleration for OCR'd documents
-- CREATE INDEX IF NOT EXISTS idx_documents_ocr_fts
--   ON documents.documents USING gin (to_tsvector('simple', ocr_extracted_text))
--   WHERE ocr_extracted_text IS NOT NULL;

-- =============================================================
-- End of 16
-- =============================================================


-- =============================================================
-- 17. Materialized Views (Analytics Layer)
-- Run on the read replica for performance
-- =============================================================

CREATE SCHEMA IF NOT EXISTS analytics;
SET search_path TO analytics, public;

-- =============================================================
-- 17.1 Student Performance Trend
-- Per-student quarterly average across all subjects
-- =============================================================
CREATE MATERIALIZED VIEW analytics.mv_student_performance_trend AS
SELECT
  se.tenant_id,
  se.school_year_id,
  se.student_id,
  s.first_name || ' ' || s.last_name AS student_name,
  se.grade_level_id,
  se.section_id,
  gp.period_type,
  gp.name AS period_name,
  count(DISTINCT cg.subject_id) AS subjects_with_grades,
  avg(cg.transmuted_grade) AS avg_transmuted_grade,
  min(cg.transmuted_grade) AS min_transmuted_grade,
  max(cg.transmuted_grade) AS max_transmuted_grade,
  count(*) FILTER (WHERE cg.transmuted_grade >= 90) AS subjects_outstanding,
  count(*) FILTER (WHERE cg.transmuted_grade >= 75) AS subjects_passing,
  count(*) FILTER (WHERE cg.transmuted_grade < 75) AS subjects_failing,
  now() AS computed_at
FROM sis.student_enrollments se
JOIN sis.students s ON s.id = se.student_id
JOIN gradebook.computed_grades cg ON cg.student_id = se.student_id
JOIN gradebook.grading_periods gp ON gp.id = cg.grading_period_id
WHERE se.deleted_at IS NULL
  AND s.deleted_at IS NULL
  AND cg.deleted_at IS NULL
GROUP BY se.tenant_id, se.school_year_id, se.student_id, s.first_name, s.last_name,
         se.grade_level_id, se.section_id, gp.period_type, gp.name;

CREATE UNIQUE INDEX idx_mv_spt_pk ON analytics.mv_student_performance_trend
  (tenant_id, school_year_id, student_id, period_type);
CREATE INDEX idx_mv_spt_tenant_grade ON analytics.mv_student_performance_trend(tenant_id, grade_level_id);
CREATE INDEX idx_mv_spt_tenant_section ON analytics.mv_student_performance_trend(tenant_id, section_id);

COMMENT ON MATERIALIZED VIEW analytics.mv_student_performance_trend IS 'Refresh nightly via pg_cron: REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_student_performance_trend;';

-- =============================================================
-- 17.2 Daily Attendance Rollup
-- =============================================================
CREATE MATERIALIZED VIEW analytics.mv_attendance_daily AS
SELECT
  ar.tenant_id,
  ar.school_year_id,
  ar.attendance_date,
  se.grade_level_id,
  se.section_id,
  count(*) AS total_students,
  count(*) FILTER (WHERE ar.status = 'present') AS present_count,
  count(*) FILTER (WHERE ar.status = 'absent') AS absent_count,
  count(*) FILTER (WHERE ar.status = 'late') AS late_count,
  count(*) FILTER (WHERE ar.status = 'excused') AS excused_count,
  ROUND(100.0 * count(*) FILTER (WHERE ar.status IN ('present','late')) / NULLIF(count(*), 0), 2) AS attendance_rate_pct
FROM sis.attendance_records ar
JOIN sis.student_enrollments se ON se.student_id = ar.student_id
  AND se.school_year_id = ar.school_year_id
  AND se.deleted_at IS NULL
WHERE ar.deleted_at IS NULL
GROUP BY ar.tenant_id, ar.school_year_id, ar.attendance_date, se.grade_level_id, se.section_id;

CREATE UNIQUE INDEX idx_mv_ad_pk ON analytics.mv_attendance_daily
  (tenant_id, school_year_id, attendance_date, grade_level_id, section_id);
CREATE INDEX idx_mv_ad_tenant_date ON analytics.mv_attendance_daily(tenant_id, attendance_date);

-- =============================================================
-- 17.3 Teacher Productivity
-- =============================================================
CREATE MATERIALIZED VIEW analytics.mv_teacher_productivity AS
SELECT
  ura.tenant_id,
  ura.user_id,
  up.first_name || ' ' || up.last_name AS teacher_name,
  up.employee_id,
  sy.label AS school_year_label,
  -- Lesson plan counts
  count(DISTINCT lp.id) FILTER (WHERE lp.deleted_at IS NULL) AS total_lesson_plans,
  count(DISTINCT lp.id) FILTER (WHERE lp.status = 'approved' AND lp.deleted_at IS NULL) AS approved_lesson_plans,
  count(DISTINCT lp.id) FILTER (WHERE lp.ai_generated = TRUE) AS ai_assisted_lesson_plans,
  -- Assessment counts
  count(DISTINCT a.id) FILTER (WHERE a.deleted_at IS NULL) AS total_assessments,
  count(DISTINCT a.id) FILTER (WHERE a.is_ai_generated = TRUE) AS ai_assisted_assessments,
  -- Grade counts
  count(DISTINCT ss.id) AS total_scores_recorded,
  -- School form counts
  count(DISTINCT sf.id) FILTER (WHERE sf.deleted_at IS NULL) AS total_forms,
  -- Communication counts
  count(DISTINCT c.id) FILTER (WHERE c.deleted_at IS NULL) AS total_communications,
  -- AI usage
  count(DISTINCT ar.id) AS total_ai_runs,
  sum(ar.total_tokens) AS total_tokens_used,
  sum(ar.cost_cents) AS total_cost_cents,
  now() AS computed_at
FROM core.user_role_assignments ura
JOIN core.users u ON u.id = ura.user_id
LEFT JOIN core.user_profiles up ON up.user_id = u.id
LEFT JOIN core.school_years sy ON sy.id::text = (ura.metadata->>'school_year_id')
LEFT JOIN academic.lesson_plans lp ON lp.teacher_user_id = u.id
  AND lp.tenant_id = ura.tenant_id
LEFT JOIN assessment.assessments a ON a.teacher_user_id = u.id
  AND a.tenant_id = ura.tenant_id
LEFT JOIN gradebook.student_scores ss ON ss.recorded_by = u.id
LEFT JOIN forms.school_forms sf ON sf.tenant_id = ura.tenant_id
LEFT JOIN comms.communications c ON c.tenant_id = ura.tenant_id
LEFT JOIN ai.agent_runs ar ON ar.triggered_by_user_id = u.id
WHERE ura.role_id IN (SELECT id FROM core.roles WHERE code = 'teacher')
  AND ura.status = 'active'
  AND ura.deleted_at IS NULL
GROUP BY ura.tenant_id, ura.user_id, up.first_name, up.last_name, up.employee_id, sy.label;

CREATE UNIQUE INDEX idx_mv_tp_pk ON analytics.mv_teacher_productivity(tenant_id, user_id, school_year_label);
CREATE INDEX idx_mv_tp_tenant ON analytics.mv_teacher_productivity(tenant_id);

-- =============================================================
-- 17.4 School Compliance Score
-- Per-school rollup of form completion
-- =============================================================
CREATE MATERIALIZED VIEW analytics.mv_school_compliance AS
SELECT
  sf.tenant_id,
  sf.school_year_id,
  -- SF1 (School Register)
  count(DISTINCT sf.id) FILTER (WHERE sf.form_code = 'SF1' AND sf.deleted_at IS NULL) AS sf1_count,
  count(DISTINCT sf.id) FILTER (WHERE sf.form_code = 'SF1' AND sf.status IN ('approved','submitted_to_deped','locked')) AS sf1_completed,
  -- SF2 (Daily Attendance)
  count(DISTINCT sf.id) FILTER (WHERE sf.form_code = 'SF2' AND sf.deleted_at IS NULL) AS sf2_count,
  count(DISTINCT sf.id) FILTER (WHERE sf.form_code = 'SF2' AND sf.status IN ('approved','submitted_to_deped','locked')) AS sf2_completed,
  -- SF5, SF9, SF10
  count(DISTINCT sf.id) FILTER (WHERE sf.form_code = 'SF5' AND sf.deleted_at IS NULL) AS sf5_count,
  count(DISTINCT sf.id) FILTER (WHERE sf.form_code = 'SF5' AND sf.status IN ('approved','submitted_to_deped','locked')) AS sf5_completed,
  count(DISTINCT sf.id) FILTER (WHERE sf.form_code = 'SF9' AND sf.deleted_at IS NULL) AS sf9_count,
  count(DISTINCT sf.id) FILTER (WHERE sf.form_code = 'SF9' AND sf.status IN ('approved','submitted_to_deped','locked')) AS sf9_completed,
  count(DISTINCT sf.id) FILTER (WHERE sf.form_code = 'SF10' AND sf.deleted_at IS NULL) AS sf10_count,
  count(DISTINCT sf.id) FILTER (WHERE sf.form_code = 'SF10' AND sf.status IN ('approved','submitted_to_deped','locked')) AS sf10_completed,
  now() AS computed_at
FROM forms.school_forms sf
WHERE sf.deleted_at IS NULL
GROUP BY sf.tenant_id, sf.school_year_id;

CREATE UNIQUE INDEX idx_mv_sc_pk ON analytics.mv_school_compliance(tenant_id, school_year_id);

-- =============================================================
-- 17.5 At-Risk Students
-- =============================================================
CREATE MATERIALIZED VIEW analytics.mv_at_risk_students AS
SELECT
  ra.tenant_id,
  ra.school_year_id,
  ra.student_id,
  s.first_name || ' ' || s.last_name AS student_name,
  s.LRN,
  se.grade_level_id,
  se.section_id,
  ra.overall_level,
  ra.overall_score,
  ra.academic_level,
  ra.attendance_level,
  ra.behavioral_level,
  ra.social_emotional_level,
  ra.trend,
  -- Open intervention cases
  (SELECT count(*) FROM intervention.intervention_cases ic
   WHERE ic.student_id = ra.student_id
     AND ic.status IN ('open','in_progress','escalated')
     AND ic.deleted_at IS NULL) AS open_cases,
  ra.assessment_date AS last_assessment_at
FROM intervention.risk_assessments ra
JOIN sis.students s ON s.id = ra.student_id
LEFT JOIN sis.student_enrollments se ON se.student_id = ra.student_id
  AND se.deleted_at IS NULL
WHERE ra.overall_level IN ('high', 'critical')
  AND ra.deleted_at IS NULL;

CREATE UNIQUE INDEX idx_mv_ars_pk ON analytics.mv_at_risk_students(tenant_id, student_id);
CREATE INDEX idx_mv_ars_level ON analytics.mv_at_risk_students(tenant_id, overall_level);
CREATE INDEX idx_mv_ars_section ON analytics.mv_at_risk_students(tenant_id, section_id);

-- =============================================================
-- 17.6 pg_cron Jobs (for refreshing materialized views)
-- =============================================================
-- Requires pg_cron extension
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
--
-- SELECT cron.schedule('refresh_performance_trend', '0 2 * * *', $$
--   REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_student_performance_trend;
-- $$);
--
-- SELECT cron.schedule('refresh_attendance', '0 2 * * *', $$
--   REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_attendance_daily;
-- $$);
--
-- SELECT cron.schedule('refresh_teacher_productivity', '0 3 * * *', $$
--   REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_teacher_productivity;
-- $$);
--
-- SELECT cron.schedule('refresh_school_compliance', '0 3 * * *', $$
--   REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_school_compliance;
-- $$);
--
-- SELECT cron.schedule('refresh_at_risk', '*/15 * * * *', $$
--   REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_at_risk_students;
-- $$);

-- =============================================================
-- 17.7 RLS for materialized views
-- (Materialized views don't support RLS natively, but the
--  underlying tables do, so the views are safe.)
-- =============================================================
-- If you need row-level security on the materialized view,
-- wrap it in a regular view that re-applies RLS predicates:
--
-- CREATE VIEW analytics.v_student_performance_trend AS
-- SELECT * FROM analytics.mv_student_performance_trend
-- WHERE tenant_id = core.current_tenant_id() OR core.is_system_admin();
--
-- ... or use security-barrier views.

-- =============================================================
-- End of 17
-- =============================================================
