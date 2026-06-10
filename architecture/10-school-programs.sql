-- =============================================================
-- Module 10: School Programs (Feeding, DRRM, Brigada, Events)
-- Depends on: 01-auth-organization.sql
-- Tables: programs, program_budgets, program_activities,
--         program_participants, program_reports, beneficiaries
-- =============================================================

CREATE SCHEMA IF NOT EXISTS programs;
SET search_path TO programs, sis, core, public;

CREATE TYPE program_category AS ENUM (
  'feeding',             -- School-Based Feeding Program (SBFP)
  'drrrm',               -- Disaster Risk Reduction & Management
  'brigada_eskwela',     -- National Schools Maintenance Week
  'sport_meet',
  'intramurals',
  'foundation_anniversary',
  'recognition_day',
  'literacy_month',
  'brigada_pagbasa',
  'health_nutrition',
  'mental_health_awareness',
  'parents_orientation',
  'practitioner_school',
  'research_symposium',
  'training_workshop',
  'community_outreach',
  'other'
);

CREATE TYPE program_status AS ENUM (
  'planning', 'approved', 'in_progress', 'on_hold', 'completed', 'cancelled', 'archived'
);

CREATE TYPE activity_status AS ENUM (
  'scheduled', 'in_progress', 'completed', 'cancelled', 'postponed'
);

CREATE TYPE budget_category AS ENUM (
  'food', 'supplies', 'transportation', 'venue', 'honoraria',
  'equipment', 'training', 'publicity', 'miscellaneous', 'other'
);

-- =============================================================
-- 1. programs
-- =============================================================
CREATE TABLE programs (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  school_year_id        UUID NOT NULL,
  category              program_category NOT NULL,
  name                  TEXT NOT NULL,
  description           TEXT,
  objectives            TEXT,
  target_beneficiaries  TEXT,
  start_date            DATE NOT NULL,
  end_date              DATE NOT NULL,
  status                program_status NOT NULL DEFAULT 'planning',
  budget_total          NUMERIC(12,2),
  budget_source         TEXT,                           -- 'deped_central' | 'school_moot' | 'donation' | 'lgu' | 'other'
  coordinator_user_id   UUID,
  approved_at           TIMESTAMPTZ,
  approved_by           UUID,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_prog_tenant ON programs(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_prog_sy ON programs(tenant_id, school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_prog_category ON programs(tenant_id, category) WHERE deleted_at IS NULL;
CREATE INDEX idx_prog_status ON programs(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_prog_dates ON programs(start_date, end_date) WHERE deleted_at IS NULL;

-- =============================================================
-- 2. program_budgets
-- =============================================================
CREATE TABLE program_budgets (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  program_id            UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  category              budget_category NOT NULL,
  description           TEXT,
  allocated_amount      NUMERIC(12,2) NOT NULL,
  spent_amount          NUMERIC(12,2) NOT NULL DEFAULT 0,
  remaining_amount      NUMERIC(12,2) GENERATED ALWAYS AS
                        (allocated_amount - spent_amount) STORED,
  receipt_url           TEXT,                           -- documents.documents.id
  approved_by           UUID,
  approved_at           TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_pb_program ON program_budgets(program_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_pb_category ON program_budgets(program_id, category) WHERE deleted_at IS NULL;

-- =============================================================
-- 3. program_activities
-- =============================================================
CREATE TABLE program_activities (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  program_id            UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  title                 TEXT NOT NULL,
  description           TEXT,
  activity_date         DATE NOT NULL,
  start_time            TIME,
  end_time              TIME,
  location              TEXT,
  facilitator           TEXT,
  status                activity_status NOT NULL DEFAULT 'scheduled',
  expected_attendees    INT,
  actual_attendees      INT,
  budget_line_id        UUID REFERENCES program_budgets(id) ON DELETE SET NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_pa_program ON program_activities(program_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_pa_date ON program_activities(activity_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_pa_status ON program_activities(program_id, status) WHERE deleted_at IS NULL;

-- =============================================================
-- 4. program_participants
-- =============================================================
CREATE TABLE program_participants (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  program_id            UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  activity_id           UUID REFERENCES program_activities(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  participant_type      TEXT NOT NULL,                  -- 'student' | 'teacher' | 'parent' | 'external'
  student_id            UUID,
  user_id               UUID,
  participant_name      TEXT NOT NULL,
  participant_contact   TEXT,
  attended              BOOLEAN NOT NULL DEFAULT FALSE,
  attended_at           TIMESTAMPTZ,
  role                  TEXT,                           -- 'volunteer' | 'beneficiary' | 'facilitator' | 'observer'
  notes                 TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_pp_program ON program_participants(program_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_pp_activity ON program_participants(activity_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_pp_student ON program_participants(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_pp_attended ON program_participants(program_id, attended) WHERE deleted_at IS NULL;

-- =============================================================
-- 5. beneficiaries  (separate from participants for analytics)
-- =============================================================
CREATE TABLE beneficiaries (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  program_id            UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  student_id            UUID NOT NULL,
  enrolled_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  enrolled_by           UUID,
  unenrolled_at         TIMESTAMPTZ,
  unenrollment_reason   TEXT,
  nutritional_status    TEXT,                           -- for feeding program: 'normal' | 'underweight' | 'severely_underweight'
  height_cm             NUMERIC(5,1),
  weight_kg             NUMERIC(5,1),
  bmi                   NUMERIC(4,1),
  measurement_date      DATE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  UNIQUE (program_id, student_id)
);

CREATE INDEX idx_ben_program ON beneficiaries(program_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ben_student ON beneficiaries(student_id) WHERE deleted_at IS NULL;

-- =============================================================
-- 6. program_reports
-- =============================================================
CREATE TABLE program_reports (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  program_id            UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  title                 TEXT NOT NULL,
  summary               TEXT,
  outcomes              TEXT,
  challenges            TEXT,
  recommendations       TEXT,
  total_participants    INT,
  total_budget          NUMERIC(12,2),
  total_spent           NUMERIC(12,2),
  photos                UUID[],
  report_data           JSONB NOT NULL DEFAULT '{}'::jsonb,
  status                program_status NOT NULL DEFAULT 'completed',
  submitted_at          TIMESTAMPTZ,
  approved_at           TIMESTAMPTZ,
  approved_by           UUID,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_pr_program ON program_reports(program_id) WHERE deleted_at IS NULL;

-- =============================================================
-- 7. RLS
-- =============================================================
ALTER TABLE programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE programs FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_prog_read ON programs
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_prog_write ON programs
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE program_budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE program_budgets FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_pb_read ON program_budgets
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_pb_write ON program_budgets
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE program_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE program_activities FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_pa_read ON program_activities
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_pa_write ON program_activities
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE program_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE program_participants FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_pp_read ON program_participants
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_pp_write ON program_participants
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE beneficiaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE beneficiaries FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ben_read ON beneficiaries
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ben_write ON beneficiaries
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE program_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE program_reports FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_pr_read ON program_reports
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_pr_write ON program_reports
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

-- =============================================================
-- 8. Triggers
-- =============================================================
DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'programs', 'program_budgets', 'program_activities',
    'program_participants', 'beneficiaries', 'program_reports'
  ])
  LOOP
    EXECUTE format('
      CREATE TRIGGER tg_set_updated_at BEFORE UPDATE ON programs.%I
        FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
    ', t);
  END LOOP;
END $$;

-- =============================================================
-- End of Module 10
-- =============================================================
