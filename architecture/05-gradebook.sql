-- =============================================================
-- Module 5: Gradebook System
-- Depends on: 01-auth-organization.sql, 04-assessments.sql
-- Tables: grading_periods, grade_categories, grade_weights,
--         student_scores, computed_grades, grade_adjustments,
--         report_cards, report_card_items
-- Notes: DepEd uses 4 quarters. Grades are quarterly (raw + transmuted)
--        with final grade computed at end of SY.
-- =============================================================

CREATE SCHEMA IF NOT EXISTS gradebook;
SET search_path TO gradebook, academic, core, public;

-- =============================================================
-- ENUMS
-- =============================================================
CREATE TYPE grading_period_type AS ENUM (
  'quarter_1', 'quarter_2', 'quarter_3', 'quarter_4', 'final', 'midterm'
);

CREATE TYPE grade_category_kind AS ENUM (
  'written_works',    -- DepEd: 25-30% (typically 25%)
  'performance_tasks',-- DepEd: 40-50% (typically 50%)
  'quarterly_assessment', -- DepEd: 20-25% (typically 25%)
  'recitation',       -- Optional, included in performance_tasks usually
  'attendance',       -- Optional
  'project',          -- Optional
  'participation',    -- Optional
  'other'
);

CREATE TYPE grade_transmutation AS ENUM (
  'deped_k12',        -- DepEd K-12 transmutation table
  'percent',          -- raw percentage
  'letter',           -- A/B/C/D/F
  'gpa',              -- 4.0 scale
  'competency_based'  -- Beginning/Developing/Average/Above Average/Outstanding
);

CREATE TYPE grade_status AS ENUM (
  'draft', 'in_progress', 'pending_review', 'approved', 'released', 'rejected'
);

CREATE TYPE report_card_status AS ENUM (
  'draft', 'pending_review', 'approved', 'released', 'archived'
);

-- =============================================================
-- 1. grading_periods
-- =============================================================
CREATE TABLE grading_periods (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  school_year_id        UUID NOT NULL,
  period_type           grading_period_type NOT NULL,
  name                  TEXT NOT NULL,                  -- '1st Quarter', 'Q1'
  start_date            DATE NOT NULL,
  end_date              DATE NOT NULL,
  is_closed             BOOLEAN NOT NULL DEFAULT FALSE,
  closed_at             TIMESTAMPTZ,
  closed_by             UUID,
  display_order         INT NOT NULL DEFAULT 0,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  UNIQUE (tenant_id, school_year_id, period_type)
);

CREATE INDEX idx_gp_tenant_sy ON grading_periods(tenant_id, school_year_id) WHERE deleted_at IS NULL;

-- =============================================================
-- 2. grade_categories  (per subject per SY)
-- =============================================================
CREATE TABLE grade_categories (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  subject_id            UUID NOT NULL,
  grade_level           INT NOT NULL,
  kind                  grade_category_kind NOT NULL,
  name                  TEXT NOT NULL,                  -- 'Written Works', 'Performance Task'
  deped_default_weight  NUMERIC(5,2) NOT NULL,          -- e.g., 25.00 for written_works
  actual_weight         NUMERIC(5,2) NOT NULL,          -- may differ per teacher
  display_order         INT NOT NULL DEFAULT 0,
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (tenant_id, school_year_id, subject_id, grade_level, kind)
);

CREATE INDEX idx_gc_tenant_subject ON grade_categories(tenant_id, subject_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_gc_grade ON grade_categories(tenant_id, grade_level) WHERE deleted_at IS NULL;

-- =============================================================
-- 3. grade_weights  (per grading period - allows per-quarter overrides)
-- =============================================================
CREATE TABLE grade_weights (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  grade_category_id     UUID NOT NULL REFERENCES grade_categories(id) ON DELETE CASCADE,
  grading_period_id     UUID NOT NULL REFERENCES grading_periods(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  weight                NUMERIC(5,2) NOT NULL,          -- override of actual_weight
  UNIQUE (grade_category_id, grading_period_id)
);

-- =============================================================
-- 4. student_scores  (raw scores per assessment per category)
-- =============================================================
CREATE TABLE student_scores (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  grading_period_id     UUID NOT NULL REFERENCES grading_periods(id) ON DELETE RESTRICT,
  student_id            UUID NOT NULL,                  -- sis.students.id
  subject_id            UUID NOT NULL,
  grade_level           INT NOT NULL,
  section_id            UUID,
  grade_category_id     UUID NOT NULL REFERENCES grade_categories(id) ON DELETE RESTRICT,
  assessment_result_id  UUID,                           -- assessment.assessment_results.id
  raw_score             NUMERIC(7,2) NOT NULL,
  total_points          NUMERIC(7,2) NOT NULL,
  percentage            NUMERIC(5,2) GENERATED ALWAYS AS
                        (CASE WHEN total_points > 0 THEN ROUND(100.0 * raw_score / total_points, 2) ELSE 0 END) STORED,
  weighted_score        NUMERIC(7,2) GENERATED ALWAYS AS
                        (ROUND(raw_score / total_points * 100 * (SELECT actual_weight FROM grade_categories WHERE id = grade_category_id) / 100, 2) ) STORED,
  recorded_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  recorded_by           UUID NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_ss_tenant_sy ON student_scores(tenant_id, school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ss_student ON student_scores(student_id, school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ss_subject_period ON student_scores(subject_id, grading_period_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ss_section ON student_scores(section_id, grading_period_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ss_category ON student_scores(grade_category_id) WHERE deleted_at IS NULL;

COMMENT ON TABLE student_scores IS 'Raw scores. percentage and weighted_score are generated columns. The actual final grade is computed by computed_grades.';

-- =============================================================
-- 5. computed_grades  (final per-period per-student per-subject)
-- =============================================================
CREATE TABLE computed_grades (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  grading_period_id     UUID NOT NULL REFERENCES grading_periods(id) ON DELETE RESTRICT,
  student_id            UUID NOT NULL,
  subject_id            UUID NOT NULL,
  initial_grade         NUMERIC(6,2),                   -- 0-100
  transmuted_grade      NUMERIC(6,2),                   -- DepEd-transmuted: 60-100
  deped_rating          TEXT,                           -- 'Outstanding' | 'Very Satisfactory' | ...
  remarks               TEXT,
  status                grade_status NOT NULL DEFAULT 'draft',
  computed_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  computed_by           UUID,                           -- user or 'system'
  approved_at           TIMESTAMPTZ,
  approved_by           UUID,
  released_at           TIMESTAMPTZ,
  released_by           UUID,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  UNIQUE (student_id, subject_id, grading_period_id)
);

CREATE INDEX idx_cg_tenant_period ON computed_grades(tenant_id, grading_period_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_cg_student_sy ON computed_grades(student_id, school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_cg_status ON computed_grades(tenant_id, status) WHERE deleted_at IS NULL;
-- Issue 9 fix: composite index for report-card generation queries
CREATE INDEX idx_cg_student_period_status ON computed_grades(student_id, grading_period_id, status) WHERE deleted_at IS NULL;

-- =============================================================
-- 6. grade_adjustments  (manual overrides with audit trail)
-- =============================================================
CREATE TABLE grade_adjustments (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  computed_grade_id     UUID NOT NULL REFERENCES computed_grades(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  original_initial      NUMERIC(6,2),
  original_transmuted   NUMERIC(6,2),
  new_initial           NUMERIC(6,2),
  new_transmuted        NUMERIC(6,2),
  reason                TEXT NOT NULL,
  adjusted_by           UUID NOT NULL,
  approved_by           UUID,
  approved_at           TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_ga_grade ON grade_adjustments(computed_grade_id);
CREATE INDEX idx_ga_adjuster ON grade_adjustments(adjusted_by);

-- =============================================================
-- 7. report_cards
-- =============================================================
CREATE TABLE report_cards (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  student_id            UUID NOT NULL,
  grading_period_id     UUID,                           -- NULL for annual report card
  section_id            UUID,
  adviser_user_id       UUID,
  status                report_card_status NOT NULL DEFAULT 'draft',
  attendance_summary    JSONB,                          -- snapshot
  grade_summary         JSONB,                          -- snapshot of all computed_grades
  general_average       NUMERIC(6,2),
  transmuted_average    NUMERIC(6,2),
  deped_honors          TEXT,                           -- 'With Honors' | 'With High Honors' | 'With Highest Honors'
  promotion_status      TEXT,                           -- 'Promoted' | 'Retained' | 'Conditional' | 'Incomplete'
  adviser_remarks       TEXT,
  principal_remarks     TEXT,
  parent_signature_url  TEXT,
  released_at           TIMESTAMPTZ,
  released_by           UUID,
  approved_at           TIMESTAMPTZ,
  approved_by           UUID,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  UNIQUE (student_id, school_year_id, grading_period_id)
);

CREATE INDEX idx_rc_tenant_sy ON report_cards(tenant_id, school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_rc_student ON report_cards(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_rc_status ON report_cards(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_rc_section ON report_cards(section_id) WHERE deleted_at IS NULL;

COMMENT ON TABLE report_cards IS 'One row per student per grading period (or annual). grade_summary is a snapshot of computed_grades at the time of generation.';

-- =============================================================
-- 8. report_card_items  (per-subject line items)
-- =============================================================
CREATE TABLE report_card_items (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_card_id        UUID NOT NULL REFERENCES report_cards(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  subject_id            UUID NOT NULL,
  subject_name_snapshot TEXT NOT NULL,                  -- in case subject is renamed
  q1_grade              NUMERIC(6,2),
  q2_grade              NUMERIC(6,2),
  q3_grade              NUMERIC(6,2),
  q4_grade              NUMERIC(6,2),
  final_grade           NUMERIC(6,2),
  deped_rating          TEXT,
  remarks               TEXT,
  position              INT NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (report_card_id, subject_id)
);

CREATE INDEX idx_rci_card ON report_card_items(report_card_id, position);

-- =============================================================
-- 9. RLS
-- =============================================================
ALTER TABLE grading_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE grading_periods FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_gp_read ON grading_periods FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_gp_write ON grading_periods FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

ALTER TABLE grade_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE grade_categories FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_gc_read ON grade_categories FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_gc_write ON grade_categories FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

ALTER TABLE grade_weights ENABLE ROW LEVEL SECURITY;
ALTER TABLE grade_weights FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_gw_read ON grade_weights FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_gw_write ON grade_weights FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

ALTER TABLE student_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_scores FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ss_read ON student_scores
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ss_write ON student_scores
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE computed_grades ENABLE ROW LEVEL SECURITY;
ALTER TABLE computed_grades FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_cg_read ON computed_grades
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_cg_write ON computed_grades
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE grade_adjustments ENABLE ROW LEVEL SECURITY;
ALTER TABLE grade_adjustments FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ga_read ON grade_adjustments FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ga_write ON grade_adjustments FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

ALTER TABLE report_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_cards FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_rc_read ON report_cards
  FOR SELECT USING (
    tenant_id = core.current_tenant_id() OR core.is_system_admin()
    OR EXISTS (
      SELECT 1 FROM sis.student_enrollments se
      WHERE se.student_id = report_cards.student_id
        AND se.tenant_id = core.current_tenant_id()
        AND se.deleted_at IS NULL
    )
  );
CREATE POLICY rls_rc_write ON report_cards
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE report_card_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_card_items FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_rci_read ON report_card_items
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_rci_write ON report_card_items
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

-- =============================================================
-- 10. Triggers
-- =============================================================
DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'grading_periods', 'grade_categories', 'grade_weights',
    'student_scores', 'computed_grades', 'grade_adjustments',
    'report_cards', 'report_card_items'
  ])
  LOOP
    EXECUTE format('
      CREATE TRIGGER tg_set_updated_at BEFORE UPDATE ON gradebook.%I
        FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
    ', t);
  END LOOP;
END $$;

-- =============================================================
-- 11. DepEd transmutation function
-- =============================================================
CREATE OR REPLACE FUNCTION gradebook.deped_transmute(p_initial NUMERIC) RETURNS NUMERIC
LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE
    WHEN p_initial >= 100 THEN 100
    WHEN p_initial >= 98.40 THEN 99
    WHEN p_initial >= 96.80 THEN 98
    WHEN p_initial >= 95.20 THEN 97
    WHEN p_initial >= 93.60 THEN 96
    WHEN p_initial >= 92.00 THEN 95
    WHEN p_initial >= 90.40 THEN 94
    WHEN p_initial >= 88.80 THEN 93
    WHEN p_initial >= 87.20 THEN 92
    WHEN p_initial >= 85.60 THEN 91
    WHEN p_initial >= 84.00 THEN 90
    WHEN p_initial >= 82.40 THEN 89
    WHEN p_initial >= 80.80 THEN 88
    WHEN p_initial >= 79.20 THEN 87
    WHEN p_initial >= 77.60 THEN 86
    WHEN p_initial >= 76.00 THEN 85
    WHEN p_initial >= 74.40 THEN 84
    WHEN p_initial >= 72.80 THEN 83
    WHEN p_initial >= 71.20 THEN 82
    WHEN p_initial >= 69.60 THEN 81
    WHEN p_initial >= 68.00 THEN 80
    WHEN p_initial >= 66.40 THEN 79
    WHEN p_initial >= 64.80 THEN 78
    WHEN p_initial >= 63.20 THEN 77
    WHEN p_initial >= 61.60 THEN 76
    WHEN p_initial >= 60.00 THEN 75
    ELSE GREATEST(60, ROUND(p_initial, 0))::NUMERIC
  END;
$$;

COMMENT ON FUNCTION gradebook.deped_transmute IS 'DepEd K-12 transmutation table (DO 8, s. 2015). Maps raw 0-100 to 60-100 transmuted grade.';

-- DepEd rating labels
CREATE OR REPLACE FUNCTION gradebook.deped_rating(p_transmuted NUMERIC) RETURNS TEXT
LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE
    WHEN p_transmuted >= 90 THEN 'Outstanding'
    WHEN p_transmuted >= 85 THEN 'Very Satisfactory'
    WHEN p_transmuted >= 80 THEN 'Satisfactory'
    WHEN p_transmuted >= 75 THEN 'Fairly Satisfactory'
    ELSE 'Did Not Meet Expectations'
  END;
$$;

-- Compute a student's grade for a given period and subject
CREATE OR REPLACE FUNCTION gradebook.compute_grade(
  p_student_id    UUID,
  p_subject_id    UUID,
  p_grading_period_id UUID
) RETURNS NUMERIC
LANGUAGE plpgsql STABLE AS $$
DECLARE
  v_initial NUMERIC;
BEGIN
  -- Initial = weighted average of category percentages
  SELECT SUM(s.percentage * COALESCE(gw.weight, gc.actual_weight)) / NULLIF(SUM(COALESCE(gw.weight, gc.actual_weight)), 0)
  INTO v_initial
  FROM gradebook.student_scores s
  JOIN gradebook.grade_categories gc ON gc.id = s.grade_category_id
  LEFT JOIN gradebook.grade_weights gw ON gw.grade_category_id = gc.id AND gw.grading_period_id = s.grading_period_id
  WHERE s.student_id = p_student_id
    AND s.subject_id = p_subject_id
    AND s.grading_period_id = p_grading_period_id
    AND s.deleted_at IS NULL
    AND gc.deleted_at IS NULL;

  RETURN COALESCE(ROUND(v_initial, 2), 0);
END;
$$;

-- =============================================================
-- 12. Auto-create report_cards when computed_grades are approved
-- =============================================================
CREATE OR REPLACE FUNCTION gradebook.tg_report_card_create() RETURNS TRIGGER AS $$
DECLARE
  v_rc_id UUID;
BEGIN
  IF NEW.status = 'approved' AND (OLD.status IS NULL OR OLD.status <> 'approved') THEN
    INSERT INTO gradebook.report_cards
      (tenant_id, school_year_id, student_id, grading_period_id, status, created_by)
    VALUES
      (NEW.tenant_id, NEW.school_year_id, NEW.student_id, NEW.grading_period_id, 'pending_review', NEW.approved_by)
    ON CONFLICT (student_id, school_year_id, grading_period_id) DO NOTHING
    RETURNING id INTO v_rc_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_cg_approved_creates_rc
  AFTER UPDATE OF status ON gradebook.computed_grades
  FOR EACH ROW EXECUTE FUNCTION gradebook.tg_report_card_create();

-- =============================================================
-- End of Module 5
-- =============================================================
