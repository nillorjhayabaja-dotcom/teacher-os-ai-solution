-- =============================================================
-- Module 7: Student Risk & Intervention
-- Depends on: 01-auth-organization.sql, 02-student-information.sql
-- Tables: risk_indicators, risk_assessments, risk_score_history,
--         intervention_cases, intervention_actions, intervention_notes,
--         intervention_referrals
-- =============================================================

CREATE SCHEMA IF NOT EXISTS intervention;
SET search_path TO intervention, sis, core, public;

-- =============================================================
-- ENUMS
-- =============================================================
CREATE TYPE risk_level AS ENUM (
  'low', 'moderate', 'high', 'critical'
);

CREATE TYPE risk_category AS ENUM (
  'academic',           -- grades, missing work, performance
  'attendance',         -- absences, tardiness
  'behavioral',         -- discipline referrals
  'social_emotional',   -- SEL concerns
  'health',             -- medical/mental health
  'family',             -- home situation
  'language',           -- language barrier
  'special_needs',      -- SPED / 504 / IEP
  'nutrition',          -- feeding program eligibility
  'other'
);

CREATE TYPE indicator_source AS ENUM (
  'manual',             -- teacher judgment
  'attendance_data',    -- computed from attendance_records
  'grade_data',         -- computed from computed_grades
  'ai_detected',        -- AI agent flagged
  'parent_report',      -- parent/guardian
  'peer_report',        -- classmate report
  'self_report',        -- student disclosure
  'assessment_data'     -- assessment results
);

CREATE TYPE intervention_status AS ENUM (
  'open',               -- case is being worked on
  'in_progress',        -- actions underway
  'monitoring',         -- watching, no active actions
  'escalated',          -- sent to guidance/principal
  'resolved',           -- student improved
  'referred_external',  -- sent to specialist
  'closed',             -- no longer active
  'reopened'            -- case returned to active
);

CREATE TYPE intervention_priority AS ENUM (
  'low', 'medium', 'high', 'urgent'
);

CREATE TYPE intervention_action_kind AS ENUM (
  'tutoring', 'parent_meeting', 'home_visit', 'counseling_session',
  'peer_mentoring', 'resource_referral', 'iep_review', '504_review',
  'feeding_program', 'health_referral', 'social_work_referral',
  'academic_plan', 'attendance_plan', 'behavior_plan',
  'ai_recommendation', 'other'
);

CREATE TYPE intervention_action_status AS ENUM (
  'planned', 'in_progress', 'completed', 'skipped', 'cancelled', 'blocked'
);

-- =============================================================
-- 1. risk_indicators
-- =============================================================
CREATE TABLE risk_indicators (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  student_id            UUID NOT NULL,
  risk_category         risk_category NOT NULL,
  indicator_source      indicator_source NOT NULL,
  source_id             UUID,                           -- FK to attendance_records, computed_grades, etc.
  title                 TEXT NOT NULL,
  description           TEXT,
  raw_value             NUMERIC,                        -- e.g., 0.32 attendance rate
  threshold_value       NUMERIC,                        -- the threshold that was crossed
  severity              risk_level NOT NULL,
  evidence              JSONB,                          -- supporting data
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  detected_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  detected_by           UUID,                           -- NULL for system/AI detection
  resolved_at           TIMESTAMPTZ,
  resolved_by           UUID,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_ri_tenant_student ON risk_indicators(tenant_id, student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ri_active ON risk_indicators(tenant_id, is_active) WHERE is_active = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_ri_category ON risk_indicators(tenant_id, risk_category) WHERE deleted_at IS NULL;
CREATE INDEX idx_ri_severity ON risk_indicators(tenant_id, severity) WHERE deleted_at IS NULL;
CREATE INDEX idx_ri_detected ON risk_indicators(detected_at DESC) WHERE deleted_at IS NULL;

-- =============================================================
-- 2. risk_assessments  (computed risk per category per student)
-- =============================================================
CREATE TABLE risk_assessments (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  student_id            UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  assessment_date       TIMESTAMPTZ NOT NULL DEFAULT now(),
  -- Overall risk
  overall_score         NUMERIC(5,2) NOT NULL,          -- 0-100
  overall_level         risk_level NOT NULL,
  -- Per-category scores
  academic_score        NUMERIC(5,2),
  attendance_score      NUMERIC(5,2),
  behavioral_score      NUMERIC(5,2),
  social_emotional_score NUMERIC(5,2),
  -- Per-category levels
  academic_level        risk_level,
  attendance_level      risk_level,
  behavioral_level      risk_level,
  social_emotional_level risk_level,
  -- AI reasoning
  ai_generated          BOOLEAN NOT NULL DEFAULT FALSE,
  ai_run_id             UUID,                           -- ai.agent_runs.id
  ai_reasoning          JSONB,                          -- {"factors": [...], "weights": [...]}
  human_validated       BOOLEAN NOT NULL DEFAULT FALSE,
  human_validated_by    UUID,
  human_validated_at    TIMESTAMPTZ,
  human_overrides       JSONB,                          -- manual adjustments
  -- Trend
  trend                 TEXT,                            -- 'improving' | 'stable' | 'worsening'
  previous_assessment_id UUID,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_ra_tenant_student ON risk_assessments(tenant_id, student_id, assessment_date DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_ra_sy ON risk_assessments(tenant_id, school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ra_level ON risk_assessments(tenant_id, overall_level) WHERE deleted_at IS NULL;
CREATE INDEX idx_ra_high_risk ON risk_assessments(tenant_id) WHERE overall_level IN ('high', 'critical') AND deleted_at IS NULL;

COMMENT ON TABLE risk_assessments IS 'Snapshot of a student\'s risk profile at a point in time. Newer assessments supersede older ones.';

-- =============================================================
-- 3. risk_score_history  (time-series of risk for trend analysis)
-- =============================================================
CREATE TABLE risk_score_history (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  student_id            UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  recorded_date         DATE NOT NULL,
  risk_category         risk_category NOT NULL,
  score                 NUMERIC(5,2) NOT NULL,
  level                 risk_level NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (student_id, school_year_id, recorded_date, risk_category)
);

CREATE INDEX idx_rsh_student_date ON risk_score_history(student_id, recorded_date DESC);
CREATE INDEX idx_rsh_tenant_date ON risk_score_history(tenant_id, recorded_date DESC);

-- Partition this table by year for 1M+ students.
-- CREATE TABLE risk_score_history (LIKE risk_score_history INCLUDING ALL) PARTITION BY RANGE (recorded_date);

-- =============================================================
-- 4. intervention_cases
-- =============================================================
CREATE TABLE intervention_cases (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  student_id            UUID NOT NULL,
  risk_assessment_id    UUID REFERENCES risk_assessments(id) ON DELETE SET NULL,
  case_number           TEXT NOT NULL,                  -- e.g., 'IC-2026-0001'
  title                 TEXT NOT NULL,
  description           TEXT,
  status                intervention_status NOT NULL DEFAULT 'open',
  priority              intervention_priority NOT NULL DEFAULT 'medium',
  risk_categories       risk_category[] NOT NULL DEFAULT '{}',
  is_ai_created         BOOLEAN NOT NULL DEFAULT FALSE,
  ai_run_id             UUID,
  opened_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  opened_by             UUID NOT NULL,
  closed_at             TIMESTAMPTZ,
  closed_by             UUID,
  closure_reason        TEXT,
  assigned_to           UUID,                           -- current case owner
  assigned_at           TIMESTAMPTZ,
  escalated_to          UUID,
  escalated_at          TIMESTAMPTZ,
  escalation_reason     TEXT,
  parent_notified_at    TIMESTAMPTZ,
  parent_notified_by    UUID,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (tenant_id, case_number)
);

CREATE INDEX idx_ic_tenant ON intervention_cases(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ic_student ON intervention_cases(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ic_status ON intervention_cases(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_ic_priority ON intervention_cases(tenant_id, priority) WHERE deleted_at IS NULL;
CREATE INDEX idx_ic_assigned ON intervention_cases(assigned_to) WHERE assigned_to IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX idx_ic_opened ON intervention_cases(opened_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_ic_active_high_priority ON intervention_cases(tenant_id) WHERE status IN ('open','in_progress','escalated') AND priority IN ('high','urgent') AND deleted_at IS NULL;

-- =============================================================
-- 5. intervention_actions
-- =============================================================
CREATE TABLE intervention_actions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  intervention_case_id  UUID NOT NULL REFERENCES intervention_cases(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  action_kind           intervention_action_kind NOT NULL,
  title                 TEXT NOT NULL,
  description           TEXT,
  status                intervention_action_status NOT NULL DEFAULT 'planned',
  planned_date          DATE,
  due_date              DATE,
  completed_at          TIMESTAMPTZ,
  completed_by          UUID,
  outcome               TEXT,                           -- what actually happened
  impact_score          NUMERIC(5,2),                   -- 0-100, post-action assessment
  is_ai_suggested       BOOLEAN NOT NULL DEFAULT FALSE,
  ai_run_id             UUID,                           -- link to AI that suggested this
  assigned_to           UUID,
  documents             UUID[],                         -- attachments
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_ia_case ON intervention_actions(intervention_case_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ia_tenant ON intervention_actions(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ia_due ON intervention_actions(tenant_id, due_date) WHERE status IN ('planned','in_progress') AND deleted_at IS NULL;
CREATE INDEX idx_ia_assigned ON intervention_actions(assigned_to) WHERE assigned_to IS NOT NULL AND deleted_at IS NULL;

-- =============================================================
-- 6. intervention_notes  (free-text chronological log)
-- =============================================================
CREATE TABLE intervention_notes (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  intervention_case_id  UUID NOT NULL REFERENCES intervention_cases(id) ON DELETE CASCADE,
  intervention_action_id UUID REFERENCES intervention_actions(id) ON DELETE SET NULL,
  tenant_id             UUID NOT NULL,
  note                  TEXT NOT NULL,
  is_private            BOOLEAN NOT NULL DEFAULT FALSE, -- visible only to assigned+principal
  note_type             TEXT NOT NULL DEFAULT 'progress' CHECK (note_type IN ('progress','concern','milestone','escalation','communication','other')),
  attachments           UUID[],
  is_ai_generated       BOOLEAN NOT NULL DEFAULT FALSE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID NOT NULL,
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_in_case ON intervention_notes(intervention_case_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_in_action ON intervention_notes(intervention_action_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_in_created ON intervention_notes(created_at DESC) WHERE deleted_at IS NULL;

-- =============================================================
-- 7. intervention_referrals  (referrals to specialists/external)
-- =============================================================
CREATE TABLE intervention_referrals (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  intervention_case_id  UUID NOT NULL REFERENCES intervention_cases(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  referred_to_name      TEXT NOT NULL,                  -- 'Dr. Cruz, Pediatrician'
  referred_to_org       TEXT,                           -- 'Barangay Health Center'
  referred_to_contact   TEXT,
  referral_type         TEXT NOT NULL,                  -- 'medical' | 'psychological' | 'social_worker' | 'legal' | 'other'
  reason                TEXT NOT NULL,
  referred_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  referred_by           UUID NOT NULL,
  appointment_date      TIMESTAMPTZ,
  appointment_outcome   TEXT,
  completed_at          TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_ir_case ON intervention_referrals(intervention_case_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ir_tenant ON intervention_referrals(tenant_id) WHERE deleted_at IS NULL;

-- =============================================================
-- 8. RLS
-- =============================================================
ALTER TABLE risk_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_indicators FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ri_read ON risk_indicators
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ri_write ON risk_indicators
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE risk_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_assessments FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ra_read ON risk_assessments
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ra_write ON risk_assessments
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE risk_score_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_score_history FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_rsh_read ON risk_score_history
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_rsh_write ON risk_score_history
  FOR ALL USING (core.is_system_admin());  -- system-managed

ALTER TABLE intervention_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE intervention_cases FORCE ROW LEVEL SECURITY;
-- Cases are visible to: assigned user, principal, guidance, division staff
CREATE POLICY rls_ic_read ON intervention_cases
  FOR SELECT USING (
    tenant_id = core.current_tenant_id() OR core.is_system_admin()
    OR assigned_to = core.current_user_id()
    OR opened_by = core.current_user_id()
    OR core.current_role_code() IN ('principal','school_head','guidance','head_teacher')
  );
CREATE POLICY rls_ic_write ON intervention_cases
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE intervention_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE intervention_actions FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ia_read ON intervention_actions
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ia_write ON intervention_actions
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE intervention_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE intervention_notes FORCE ROW LEVEL SECURITY;
-- Private notes only visible to creator, assigned, and principal
CREATE POLICY rls_in_read ON intervention_notes
  FOR SELECT USING (
    (tenant_id = core.current_tenant_id() AND (NOT is_private
       OR created_by = core.current_user_id()
       OR core.current_role_code() IN ('principal','school_head','guidance')))
    OR core.is_system_admin()
  );
CREATE POLICY rls_in_write ON intervention_notes
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE intervention_referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE intervention_referrals FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ir_read ON intervention_referrals
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ir_write ON intervention_referrals
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

-- =============================================================
-- 9. Triggers
-- =============================================================
DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'risk_indicators', 'risk_assessments', 'risk_score_history',
    'intervention_cases', 'intervention_actions', 'intervention_notes',
    'intervention_referrals'
  ])
  LOOP
    EXECUTE format('
      CREATE TRIGGER tg_set_updated_at BEFORE UPDATE ON intervention.%I
        FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
    ', t);
  END LOOP;
END $$;

-- =============================================================
-- 10. Auto-generate case_number
-- =============================================================
CREATE OR REPLACE FUNCTION intervention.tg_set_case_number() RETURNS TRIGGER AS $$
DECLARE
  v_year TEXT;
  v_seq  INT;
BEGIN
  IF NEW.case_number IS NULL OR NEW.case_number = '' THEN
    v_year := to_char(NEW.opened_at, 'YYYY');
    SELECT COALESCE(MAX(CAST(SUBSTRING(case_number FROM 'IC-\d{4}-(\d+)')::TEXT AS INTEGER)), 0) + 1
    INTO v_seq
    FROM intervention.intervention_cases
    WHERE tenant_id = NEW.tenant_id
      AND case_number LIKE 'IC-' || v_year || '-%'
      AND deleted_at IS NULL;
    NEW.case_number := 'IC-' || v_year || '-' || LPAD(v_seq::TEXT, 4, '0');
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_set_case_number
  BEFORE INSERT ON intervention.intervention_cases
  FOR EACH ROW EXECUTE FUNCTION intervention.tg_set_case_number();

-- =============================================================
-- 11. Auto-create score history row when assessment is created
-- =============================================================
CREATE OR REPLACE FUNCTION intervention.tg_ra_to_history() RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO intervention.risk_score_history
    (tenant_id, student_id, school_year_id, recorded_date, risk_category, score, level)
  VALUES
    (NEW.tenant_id, NEW.student_id, NEW.school_year_id, CURRENT_DATE, 'academic', NEW.academic_score, NEW.academic_level),
    (NEW.tenant_id, NEW.student_id, NEW.school_year_id, CURRENT_DATE, 'attendance', NEW.attendance_score, NEW.attendance_level),
    (NEW.tenant_id, NEW.student_id, NEW.school_year_id, CURRENT_DATE, 'behavioral', NEW.behavioral_score, NEW.behavioral_level),
    (NEW.tenant_id, NEW.student_id, NEW.school_year_id, CURRENT_DATE, 'social_emotional', NEW.social_emotional_score, NEW.social_emotional_level)
  ON CONFLICT DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_ra_to_history
  AFTER INSERT ON intervention.risk_assessments
  FOR EACH ROW EXECUTE FUNCTION intervention.tg_ra_to_history();

-- =============================================================
-- End of Module 7
-- =============================================================
