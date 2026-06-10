-- =============================================================
-- Module 4: Assessment Management
-- Depends on: 01-auth-organization.sql
-- Tables: assessments, assessment_items, assessment_versions,
--         rubrics, rubric_criteria, rubric_levels,
--         answer_keys, assessment_results, student_responses
-- =============================================================

CREATE SCHEMA IF NOT EXISTS assessment;
SET search_path TO assessment, academic, core, public;

-- =============================================================
-- ENUMS
-- =============================================================
CREATE TYPE assessment_type AS ENUM (
  'quiz', 'unit_test', 'long_quiz', 'exam', 'midterm', 'final',
  'worksheet', 'performance_task', 'project', 'oral_exam', 'recitation',
  'homework', 'portfolio', 'lab_report', 'other'
);

CREATE TYPE assessment_category AS ENUM (
  'formative', 'summative', 'diagnostic', 'benchmark', 'mock'
);

CREATE TYPE question_type AS ENUM (
  'multiple_choice', 'true_false', 'short_answer', 'essay',
  'fill_in_blank', 'matching', 'enumeration', 'ordering',
  'drawing', 'rubric_scored', 'coding', 'computation', 'other'
);

CREATE TYPE difficulty_level AS ENUM (
  'easy', 'medium', 'hard', 'mixed'
);

CREATE TYPE scoring_method AS ENUM (
  'auto',         -- computer-graded
  'manual',       -- teacher-graded
  'hybrid'        -- computer for some items, manual for others
);

CREATE TYPE student_response_status AS ENUM (
  'not_started', 'in_progress', 'submitted', 'graded', 'returned'
);

-- =============================================================
-- 1. assessments
-- =============================================================
CREATE TABLE assessments (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  school_year_id        UUID NOT NULL,
  subject_id            UUID NOT NULL,                  -- academic.subjects.id (cross-schema)
  grade_level           INT NOT NULL,
  section_id            UUID,                           -- sis.sections.id (cross-schema)
  teacher_user_id       UUID NOT NULL,
  title                 TEXT NOT NULL,
  description           TEXT,
  assessment_type       assessment_type NOT NULL,
  assessment_category   assessment_category NOT NULL,
  quarter               INT,                            -- when in the SY
  total_points          NUMERIC(6,2) NOT NULL DEFAULT 0,
  passing_score         NUMERIC(6,2),
  duration_minutes      INT,
  instructions          TEXT,
  scoring_method        scoring_method NOT NULL DEFAULT 'hybrid',
  difficulty            difficulty_level NOT NULL DEFAULT 'medium',
  is_ai_generated       BOOLEAN NOT NULL DEFAULT FALSE,
  ai_output_id          UUID,                           -- ai.ai_outputs
  status                TEXT NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft','scheduled','open','closed','archived')),
  available_from        TIMESTAMPTZ,
  available_until       TIMESTAMPTZ,
  shuffle_questions     BOOLEAN NOT NULL DEFAULT FALSE,
  show_feedback         BOOLEAN NOT NULL DEFAULT TRUE,
  max_attempts          INT NOT NULL DEFAULT 1,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_asmt_tenant ON assessments(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_asmt_teacher ON assessments(teacher_user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_asmt_subject ON assessments(subject_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_asmt_section ON assessments(section_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_asmt_sy ON assessments(school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_asmt_status ON assessments(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_asmt_dates ON assessments(available_from, available_until) WHERE deleted_at IS NULL;

-- =============================================================
-- 2. assessment_versions  (snapshot history)
-- =============================================================
CREATE TABLE assessment_versions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id         UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  version_number        INT NOT NULL,
  questions_snapshot    JSONB NOT NULL,                 -- full snapshot
  answer_key_snapshot   JSONB,
  rubric_snapshot       JSONB,
  total_points          NUMERIC(6,2) NOT NULL,
  change_summary        TEXT,
  created_by            UUID NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (assessment_id, version_number)
);

CREATE INDEX idx_av_assessment ON assessment_versions(assessment_id);

-- =============================================================
-- 3. assessment_items  (the individual questions)
-- =============================================================
CREATE TABLE assessment_items (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id         UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  position              INT NOT NULL,
  question_type         question_type NOT NULL,
  prompt                TEXT NOT NULL,
  prompt_html           TEXT,                           -- rendered HTML
  stem_image_url        TEXT,
  options               JSONB,                          -- for MC: [{"id":"a","text":"..."}]
  correct_answer        JSONB,                          -- canonical answer (multiple correct possible)
  acceptable_answers    JSONB,                          -- list of acceptable variants
  explanation           TEXT,                           -- shown after grading
  points                NUMERIC(6,2) NOT NULL,
  partial_credit        BOOLEAN NOT NULL DEFAULT FALSE,
  difficulty            difficulty_level,
  melc_ids              UUID[],                         -- which MELCs this item assesses
  bloom_level           TEXT,
  estimated_time_seconds INT,
  is_ai_generated       BOOLEAN NOT NULL DEFAULT FALSE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (assessment_id, position)
);

CREATE INDEX idx_ai_assessment ON assessment_items(assessment_id, position) WHERE deleted_at IS NULL;
CREATE INDEX idx_ai_tenant ON assessment_items(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ai_type ON assessment_items(assessment_id, question_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_ai_melcs ON assessment_items USING gin (melc_ids) WHERE deleted_at IS NULL;

-- =============================================================
-- 4. answer_keys  (one canonical key per assessment)
-- =============================================================
CREATE TABLE answer_keys (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id         UUID NOT NULL UNIQUE REFERENCES assessments(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  answer_data           JSONB NOT NULL,                  -- {item_id: answer}
  alternate_keys        JSONB,                          -- for short-answer variants
  scoring_rules         JSONB,                          -- weights, penalties, partial credit
  is_ai_generated       BOOLEAN NOT NULL DEFAULT FALSE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_ak_tenant ON answer_keys(tenant_id) WHERE deleted_at IS NULL;

-- =============================================================
-- 5. rubrics
-- =============================================================
CREATE TABLE rubrics (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id         UUID REFERENCES assessments(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  name                  TEXT NOT NULL,
  description           TEXT,
  type                  TEXT NOT NULL DEFAULT 'analytic' CHECK (type IN ('analytic','holistic','single_point')),
  is_ai_generated       BOOLEAN NOT NULL DEFAULT FALSE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_rubrics_tenant ON rubrics(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_rubrics_assessment ON rubrics(assessment_id) WHERE deleted_at IS NULL;

-- =============================================================
-- 6. rubric_criteria
-- =============================================================
CREATE TABLE rubric_criteria (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rubric_id             UUID NOT NULL REFERENCES rubrics(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  position              INT NOT NULL,
  name                  TEXT NOT NULL,
  description           TEXT,
  max_points            NUMERIC(6,2) NOT NULL,
  weight                NUMERIC(5,2) NOT NULL DEFAULT 1.0,  -- multiplier
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  UNIQUE (rubric_id, position)
);

CREATE INDEX idx_rc_rubric ON rubric_criteria(rubric_id, position) WHERE deleted_at IS NULL;

-- =============================================================
-- 7. rubric_levels  (the cell values per criterion)
-- =============================================================
CREATE TABLE rubric_levels (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rubric_criterion_id   UUID NOT NULL REFERENCES rubric_criteria(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  level_name            TEXT NOT NULL,                  -- 'Excellent', 'Proficient', etc.
  level_order           INT NOT NULL,
  description           TEXT,
  points                NUMERIC(6,2) NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  UNIQUE (rubric_criterion_id, level_order)
);

CREATE INDEX idx_rl_criterion ON rubric_levels(rubric_criterion_id, level_order) WHERE deleted_at IS NULL;

-- =============================================================
-- 8. assessment_results  (per-student per-assessment)
-- =============================================================
CREATE TABLE assessment_results (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  assessment_id         UUID NOT NULL REFERENCES assessments(id) ON DELETE RESTRICT,
  student_id            UUID NOT NULL,                  -- sis.students.id (cross-schema)
  school_year_id        UUID NOT NULL,
  attempt_number        INT NOT NULL DEFAULT 1,
  status                student_response_status NOT NULL DEFAULT 'not_started',
  started_at            TIMESTAMPTZ,
  submitted_at          TIMESTAMPTZ,
  graded_at             TIMESTAMPTZ,
  graded_by             UUID,
  raw_score             NUMERIC(7,2),
  total_points          NUMERIC(7,2) NOT NULL,
  percentage            NUMERIC(5,2) GENERATED ALWAYS AS
                        (CASE WHEN total_points > 0 THEN ROUND(100.0 * raw_score / total_points, 2) ELSE NULL END) STORED,
  rubric_scores         JSONB,                          -- {criterion_id: {level_id, points}}
  feedback              TEXT,
  is_ai_graded          BOOLEAN NOT NULL DEFAULT FALSE,
  ai_grading_run_id     UUID,                           -- ai.agent_runs.id
  needs_human_review    BOOLEAN NOT NULL DEFAULT FALSE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (assessment_id, student_id, attempt_number)
);

CREATE INDEX idx_ar_tenant ON assessment_results(tenant_id, school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ar_student ON assessment_results(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ar_assessment ON assessment_results(assessment_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ar_status ON assessment_results(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_ar_grading_queue ON assessment_results(assessment_id)
  WHERE status IN ('submitted','in_progress') AND deleted_at IS NULL;

COMMENT ON TABLE assessment_results IS 'One row per student per attempt. percentage is a generated column.';

-- =============================================================
-- 9. student_responses  (the per-item answers, can be many rows per result)
-- =============================================================
CREATE TABLE student_responses (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_result_id  UUID NOT NULL REFERENCES assessment_results(id) ON DELETE CASCADE,
  assessment_item_id    UUID NOT NULL REFERENCES assessment_items(id) ON DELETE RESTRICT,
  tenant_id             UUID NOT NULL,
  response_data         JSONB NOT NULL,                  -- flexible: text, choice id, drawing URL, etc.
  is_correct            BOOLEAN,                        -- NULL for manual grading
  points_awarded        NUMERIC(6,2),
  points_possible       NUMERIC(6,2) NOT NULL,
  auto_graded           BOOLEAN NOT NULL DEFAULT FALSE,
  manual_graded_by      UUID,
  manual_graded_at      TIMESTAMPTZ,
  feedback              TEXT,
  time_spent_seconds    INT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (assessment_result_id, assessment_item_id)
);

CREATE INDEX idx_sr_result ON student_responses(assessment_result_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sr_item ON student_responses(assessment_item_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sr_grading_queue ON student_responses(assessment_item_id)
  WHERE is_correct IS NULL AND deleted_at IS NULL;

-- =============================================================
-- 10. RLS (assessment schema)
-- =============================================================
ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_asmt_read ON assessments
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_asmt_write ON assessments
  FOR ALL USING (
    tenant_id = core.current_tenant_id()
    AND (teacher_user_id = core.current_user_id() OR core.is_tenant_admin())
  );

ALTER TABLE assessment_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_av_read ON assessment_versions FOR SELECT USING (TRUE);
CREATE POLICY rls_av_write ON assessment_versions FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE assessment_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_items FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ai_read ON assessment_items
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ai_write ON assessment_items
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE answer_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE answer_keys FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ak_read ON answer_keys
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ak_write ON answer_keys
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE rubrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE rubrics FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_rub_read ON rubrics FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_rub_write ON rubrics FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE rubric_criteria ENABLE ROW LEVEL SECURITY;
ALTER TABLE rubric_criteria FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_rc_read ON rubric_criteria FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_rc_write ON rubric_criteria FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE rubric_levels ENABLE ROW LEVEL SECURITY;
ALTER TABLE rubric_levels FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_rl_read ON rubric_levels FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_rl_write ON rubric_levels FOR ALL USING (core.current_user_id() IS NOT NULL);

-- assessment_results: students can only see their own; teachers see their sections'
ALTER TABLE assessment_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_results FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ar_read ON assessment_results
  FOR SELECT USING (
    student_id::text = COALESCE(NULLIF(current_setting('app.current_student_id', true), ''), '')
    OR EXISTS (
      SELECT 1 FROM sis.student_enrollments se
      WHERE se.student_id = assessment_results.student_id
        AND se.tenant_id = core.current_tenant_id()
        AND se.deleted_at IS NULL
    )
    OR core.is_tenant_admin() OR core.is_system_admin()
  );
CREATE POLICY rls_ar_write ON assessment_results
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE student_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_responses FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_sr_read ON student_responses
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_sr_write ON student_responses
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

-- =============================================================
-- 11. Triggers
-- =============================================================
DO $$
DECLARE
  t TEXT;
BEGIN
  FOR t IN
    SELECT unnest(ARRAY[
      'assessments', 'assessment_versions', 'assessment_items',
      'answer_keys', 'rubrics', 'rubric_criteria', 'rubric_levels',
      'assessment_results', 'student_responses'
    ])
  LOOP
    EXECUTE format('
      CREATE TRIGGER tg_set_updated_at
        BEFORE UPDATE ON assessment.%I
        FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
    ', t);
  END LOOP;
END $$;

-- =============================================================
-- End of Module 4
-- =============================================================
