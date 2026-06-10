-- =============================================================
-- Module 9: Reporting & Compliance (RPMS, Accomplishment Reports)
-- Depends on: 01-auth-organization.sql
-- Tables: report_templates, reports, report_versions,
--         evidence_files, report_submissions, kpi_metrics
-- =============================================================

CREATE SCHEMA IF NOT EXISTS compliance;
SET search_path TO compliance, core, public;

-- =============================================================
-- ENUMS
-- =============================================================
CREATE TYPE report_kind AS ENUM (
  'rpms',                    -- Results-Based Performance Management System
  'accomplishment_report',
  'narrative_report',
  'attendance_report',
  'grade_summary',
  'school_profile',
  'performance_indicator',
  'compliance_checklist',
  'other'
);

CREATE TYPE report_period AS ENUM (
  'weekly', 'monthly', 'quarterly', 'semi_annual', 'annual', 'one_time'
);

CREATE TYPE report_status AS ENUM (
  'draft', 'in_progress', 'pending_review', 'approved',
  'rejected', 'submitted', 'locked', 'archived'
);

CREATE TYPE rpms_indicator AS ENUM (
  'classroom_observation',          -- RPMS Phase II: Classroom Observation Tool (COT)
  'portfolio_assessment',          -- RPMS Phase II: Portfolio Assessment
  'attainment_of_learning_outcomes', -- RPMS Phase III
  'learners_progress',             -- Phase III
  'teacher_reflection',            -- Plus Factor
  'professional_development',      -- Plus Factor
  'community_involvement',         -- Plus Factor
  'research_innovation'            -- Plus Factor
);

-- =============================================================
-- 1. report_templates
-- =============================================================
CREATE TABLE report_templates (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,                           -- NULL for DepEd-issued
  kind                  report_kind NOT NULL,
  name                  TEXT NOT NULL,
  description           TEXT,
  version               TEXT NOT NULL DEFAULT '1.0',
  is_official           BOOLEAN NOT NULL DEFAULT FALSE,
  schema_definition     JSONB NOT NULL,                  -- what fields the report has
  field_definitions     JSONB NOT NULL,
  layout_definition     JSONB,
  required_kpis         TEXT[] NOT NULL DEFAULT '{}',   -- which KPIs must be in the report
  effective_from        DATE,
  effective_until       DATE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_rt_tenant ON report_templates(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_rt_kind ON report_templates(kind) WHERE deleted_at IS NULL;

-- =============================================================
-- 2. reports  (one instance of a report)
-- =============================================================
CREATE TABLE reports (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  template_id           UUID NOT NULL REFERENCES report_templates(id) ON DELETE RESTRICT,
  kind                  report_kind NOT NULL,           -- denormalized
  title                 TEXT NOT NULL,
  period                report_period NOT NULL,
  period_start          DATE NOT NULL,
  period_end            DATE NOT NULL,
  subject_id            UUID,                           -- if subject-specific
  grade_level           INT,
  section_id            UUID,
  prepared_by           UUID NOT NULL,
  status                report_status NOT NULL DEFAULT 'draft',
  -- Report content
  report_data           JSONB NOT NULL DEFAULT '{}'::jsonb,
  computed_at           TIMESTAMPTZ,
  computed_summary      JSONB,                          -- pre-computed KPIs
  -- Workflow
  submitted_at          TIMESTAMPTZ,
  submitted_by          UUID,
  approved_at           TIMESTAMPTZ,
  approved_by           UUID,
  rejected_at           TIMESTAMPTZ,
  rejected_by           UUID,
  rejection_reason      TEXT,
  -- Locking
  locked_at             TIMESTAMPTZ,
  locked_by             UUID,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_r_tenant ON reports(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_r_template ON reports(template_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_r_kind ON reports(tenant_id, kind) WHERE deleted_at IS NULL;
CREATE INDEX idx_r_period ON reports(period_start, period_end) WHERE deleted_at IS NULL;
CREATE INDEX idx_r_status ON reports(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_r_school_year ON reports(tenant_id, school_year_id) WHERE deleted_at IS NULL;

-- =============================================================
-- 3. report_versions  (immutable snapshot history)
-- =============================================================
CREATE TABLE report_versions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id             UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  version_number        INT NOT NULL,
  data_snapshot         JSONB NOT NULL,
  summary_snapshot      JSONB,
  change_summary        TEXT,
  created_by            UUID NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (report_id, version_number)
);

CREATE INDEX idx_rv_report ON report_versions(report_id);

-- =============================================================
-- 4. evidence_files  (attachments supporting a report)
-- =============================================================
CREATE TABLE evidence_files (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id             UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  document_id           UUID,                           -- documents.documents.id
  field_path            TEXT,                           -- which report field this evidence supports
  description           TEXT,
  uploaded_by           UUID NOT NULL,
  uploaded_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ef_report ON evidence_files(report_id);
CREATE INDEX idx_ef_tenant ON evidence_files(tenant_id);

-- =============================================================
-- 5. report_submissions  (every time a report is submitted to DepEd)
-- =============================================================
CREATE TABLE report_submissions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id             UUID NOT NULL REFERENCES reports(id) ON DELETE RESTRICT,
  tenant_id             UUID NOT NULL,
  submitted_to          TEXT NOT NULL,                  -- 'deped_central' | 'region' | 'division' | 'district'
  submitted_by          UUID NOT NULL,
  submitted_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  submission_method     TEXT,                           -- 'online_portal' | 'email' | 'in_person' | 'api'
  reference_number      TEXT,                           -- DepEd's tracking number
  acknowledgment        TEXT,
  acknowledged_at       TIMESTAMPTZ,
  attachments           UUID[],
  external_url          TEXT,
  status                TEXT NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted','received','accepted','rejected','resubmitted')),
  rejection_reason      TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_rs_report ON report_submissions(report_id);
CREATE INDEX idx_rs_tenant ON report_submissions(tenant_id, submitted_at DESC);

-- =============================================================
-- 6. kpi_metrics  (time-series of compliance KPIs per school)
-- =============================================================
CREATE TABLE kpi_metrics (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  metric_code           TEXT NOT NULL,                  -- 'sf1_completeness', 'attendance_rate'
  metric_value          NUMERIC NOT NULL,
  metric_target         NUMERIC,                        -- the target value
  metric_unit           TEXT,                           -- '%', 'count', 'days'
  computed_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  period_start          DATE NOT NULL,
  period_end            DATE NOT NULL,
  details               JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_kpi_tenant ON kpi_metrics(tenant_id, metric_code) WHERE metric_code IS NOT NULL;
CREATE INDEX idx_kpi_period ON kpi_metrics(tenant_id, period_start, period_end);
CREATE INDEX idx_kpi_code ON kpi_metrics(metric_code, computed_at DESC);

-- =============================================================
-- 7. RLS
-- =============================================================
ALTER TABLE report_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_templates FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_rt_read ON report_templates
  FOR SELECT USING (tenant_id IS NULL OR tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_rt_write ON report_templates
  FOR ALL USING (core.is_system_admin() OR (core.current_user_id() IS NOT NULL AND NOT is_official));

ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_r_read ON reports
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_r_write ON reports
  FOR ALL USING (tenant_id = core.current_tenant_id() AND (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL));

ALTER TABLE report_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_rv_read ON report_versions
  FOR SELECT USING (EXISTS (
    SELECT 1 FROM compliance.reports r
    WHERE r.id = report_versions.report_id
      AND (r.tenant_id = core.current_tenant_id() OR core.is_system_admin())
  ));
CREATE POLICY rls_rv_write ON report_versions
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE evidence_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_files FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ef_read ON evidence_files
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ef_write ON evidence_files
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE report_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_submissions FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_rs_read ON report_submissions
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_rs_write ON report_submissions
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

ALTER TABLE kpi_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpi_metrics FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_kpi_read ON kpi_metrics
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_kpi_write ON kpi_metrics
  FOR ALL USING (core.is_system_admin());  -- computed by jobs

-- =============================================================
-- 8. Triggers
-- =============================================================
DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'report_templates', 'reports', 'report_versions',
    'evidence_files', 'report_submissions', 'kpi_metrics'
  ])
  LOOP
    EXECUTE format('
      CREATE TRIGGER tg_set_updated_at BEFORE UPDATE ON compliance.%I
        FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
    ', t);
  END LOOP;
END $$;

-- =============================================================
-- End of Module 9
-- =============================================================
