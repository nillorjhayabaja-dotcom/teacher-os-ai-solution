-- =============================================================
-- Module 3: Lesson Planning System
-- Depends on: 01-auth-organization.sql
-- Tables: subjects, melcs, learning_competencies, lesson_plans,
--         lesson_versions, lesson_templates, lesson_activities,
--         lesson_assessments, lesson_resources, lesson_approvals
-- =============================================================

CREATE SCHEMA IF NOT EXISTS academic;
SET search_path TO academic, core, public;

-- =============================================================
-- ENUMS
-- =============================================================
CREATE TYPE subject_area AS ENUM (
  'math', 'science', 'english', 'filipino', 'araling_panlipunan',
  'mapeh', 'esped', 'tle', 'values_education', 'homeroom',
  'research', 'other'
);

CREATE TYPE learning_area_stage AS ENUM (
  'kinder', 'elementary', 'junior_high', 'senior_high', 'sped'
);

CREATE TYPE lesson_status AS ENUM (
  'draft',           -- being edited
  'pending_review',  -- submitted, awaiting principal
  'approved',        -- approved by principal
  'rejected',        -- rejected, needs revision
  'archived',        -- no longer in use
  'taught'           -- was used in a class session
);

CREATE TYPE dll_component AS ENUM (
  'objectives',
  'subject_matter',
  'procedure',
  'realia',
  'remarks',
  'reflection'
);

CREATE TYPE activity_type AS ENUM (
  'motivation', 'review', 'presentation', 'discussion',
  'application', 'generalization', 'evaluation', 'assignment',
  'enrichment', 'remediation', 'group_work', 'individual_work',
  'performance_task', 'recitation', 'drill', 'game'
);

CREATE TYPE resource_type AS ENUM (
  'video', 'image', 'document', 'worksheet', 'slide', 'link', 'audio', 'interactive', 'other'
);

-- =============================================================
-- 1. subjects
-- =============================================================
CREATE TABLE subjects (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,                           -- NULL for DepEd-wide reference
  code                  TEXT NOT NULL,                  -- 'MATH-6', 'SCI-7', 'EN-6'
  name                  TEXT NOT NULL,                  -- 'Mathematics 6', 'Science 7'
  area                  subject_area NOT NULL,
  stage                 learning_area_stage NOT NULL,
  grade_levels          INT[] NOT NULL DEFAULT '{}',
  is_core               BOOLEAN NOT NULL DEFAULT TRUE,
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  description           TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE UNIQUE INDEX uq_subjects_code ON subjects(code) WHERE deleted_at IS NULL;
CREATE INDEX idx_subjects_tenant ON subjects(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_subjects_area ON subjects(area) WHERE deleted_at IS NULL;

-- =============================================================
-- 2. melcs  (Most Essential Learning Competencies - DepEd)
-- =============================================================
CREATE TABLE melcs (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,                           -- NULL for DepEd-wide reference (seeded)
  subject_id            UUID NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  code                  TEXT NOT NULL,                  -- 'M6NS-Ia-86'
  competency_text       TEXT NOT NULL,
  grade_level           INT NOT NULL,
  quarter               INT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
  week                  INT,                            -- week within quarter (1-10)
  domain                TEXT,                           -- e.g., 'Numbers and Number Sense'
  subdomain             TEXT,
  bloom_level           TEXT,                           -- 'remember' | 'understand' | 'apply' | 'analyze' | 'evaluate' | 'create'
  is_essential          BOOLEAN NOT NULL DEFAULT TRUE,
  integration_notes     TEXT,
  prerequisite_melc_ids UUID[],
  related_melc_ids      UUID[],
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  deped_version         TEXT NOT NULL DEFAULT '2020',  -- tracks which DepEd MELC matrix version
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE UNIQUE INDEX uq_melcs_code ON melcs(code) WHERE deleted_at IS NULL;
CREATE INDEX idx_melcs_subject ON melcs(subject_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_melcs_grade_quarter ON melcs(grade_level, quarter) WHERE deleted_at IS NULL;
CREATE INDEX idx_melcs_text_trgm ON melcs USING gin (competency_text gin_trgm_ops) WHERE deleted_at IS NULL;

COMMENT ON TABLE melcs IS 'Most Essential Learning Competencies. DepEd-wide reference data (tenant_id IS NULL).';

-- =============================================================
-- 3. learning_competencies  (school-specific competencies derived from MELCs)
-- =============================================================
CREATE TABLE learning_competencies (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  melc_id               UUID NOT NULL REFERENCES melcs(id) ON DELETE RESTRICT,
  subject_id            UUID NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  grade_level           INT NOT NULL,
  quarter               INT NOT NULL,
  week                  INT,
  competency_text       TEXT NOT NULL,                  -- may be customized
  objectives            TEXT[],                         -- specific learning objectives
  is_modified           BOOLEAN NOT NULL DEFAULT FALSE, -- true if teacher modified from MELC
  parent_competency_id  UUID,                           -- if this is a derivative
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_lc_tenant_subject ON learning_competencies(tenant_id, subject_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lc_melc ON learning_competencies(melc_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lc_grade_quarter ON learning_competencies(grade_level, quarter) WHERE deleted_at IS NULL;

-- =============================================================
-- 4. lesson_templates  (reusable lesson plan templates)
-- =============================================================
CREATE TABLE lesson_templates (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,                           -- NULL for DepEd-wide
  name                  TEXT NOT NULL,
  description           TEXT,
  subject_id            UUID REFERENCES subjects(id) ON DELETE SET NULL,
  grade_level           INT,
  is_public             BOOLEAN NOT NULL DEFAULT FALSE, -- shareable across schools
  is_official           BOOLEAN NOT NULL DEFAULT FALSE, -- DepEd-issued template
  template_structure    JSONB NOT NULL,                 -- skeleton of objectives/procedure/etc
  default_duration_minutes INT NOT NULL DEFAULT 60,
  usage_count           INT NOT NULL DEFAULT 0,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_lt_tenant ON lesson_templates(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lt_subject ON lesson_templates(subject_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lt_public ON lesson_templates(is_public) WHERE is_public = TRUE AND deleted_at IS NULL;

-- =============================================================
-- 5. lesson_plans  (a teacher's specific DLL)
-- =============================================================
CREATE TABLE lesson_plans (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  school_year_id        UUID NOT NULL,
  subject_id            UUID NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  grade_level           INT NOT NULL,
  section_id            UUID,                           -- section this plan targets
  teacher_user_id       UUID NOT NULL,
  quarter               INT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
  week                  INT,
  scheduled_date        DATE,
  duration_minutes      INT NOT NULL DEFAULT 60,
  title                 TEXT NOT NULL,
  status                lesson_status NOT NULL DEFAULT 'draft',
  current_version_id    UUID,                           -- FK added later (circular)
  template_id           UUID REFERENCES lesson_templates(id) ON DELETE SET NULL,
  ai_generated          BOOLEAN NOT NULL DEFAULT FALSE, -- true if any portion was AI-generated
  ai_output_id          UUID REFERENCES ai.ai_outputs(id) ON DELETE SET NULL, -- link to ai.ai_outputs (cross-schema)
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_lp_tenant ON lesson_plans(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lp_teacher ON lesson_plans(teacher_user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lp_subject ON lesson_plans(subject_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lp_section ON lesson_plans(section_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lp_sy_quarter ON lesson_plans(school_year_id, quarter, week) WHERE deleted_at IS NULL;
CREATE INDEX idx_lp_status ON lesson_plans(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_lp_scheduled ON lesson_plans(scheduled_date) WHERE deleted_at IS NULL AND scheduled_date IS NOT NULL;

COMMENT ON TABLE lesson_plans IS 'A specific Daily Lesson Plan (DLL). Mutates the lesson_versions table on every change.';

-- =============================================================
-- 6. lesson_versions  (immutable snapshots of DLL content)
-- =============================================================
CREATE TABLE lesson_versions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lesson_plan_id        UUID NOT NULL REFERENCES lesson_plans(id) ON DELETE CASCADE,
  version_number        INT NOT NULL,                   -- 1, 2, 3, ...
  -- The 6 canonical DLL components (DepEd-required):
  objectives            JSONB NOT NULL DEFAULT '[]',    -- [{"text":"...", "bloom":"apply"}]
  subject_matter        JSONB NOT NULL DEFAULT '{}',    -- {"concepts":[], "references":[], "materials":[]}
  procedure             JSONB NOT NULL DEFAULT '{}',    -- {"preliminaries":[], "motivation":[], ...}
  realia                JSONB NOT NULL DEFAULT '{}',    -- {"physical":[], "digital":[]}
  remarks               TEXT,                           -- free-text teacher remarks
  reflection            JSONB NOT NULL DEFAULT '{}',    -- {"problems":[], "interventions":[], "notes":""}
  -- Pluggable structured content
  competencies          UUID[] NOT NULL DEFAULT '{}',   -- learning_competency IDs
  activities            JSONB NOT NULL DEFAULT '[]',    -- denormalized snapshot; canonical rows in lesson_activities
  assessment_plan       JSONB NOT NULL DEFAULT '{}',    -- snapshot; canonical rows in lesson_assessments
  ai_generated_fields   TEXT[] NOT NULL DEFAULT '{}',   -- which fields AI filled
  change_summary        TEXT,
  is_draft              BOOLEAN NOT NULL DEFAULT FALSE,
  created_by            UUID NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (lesson_plan_id, version_number)
);

CREATE INDEX idx_lv_plan ON lesson_versions(lesson_plan_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lv_created ON lesson_versions(created_at DESC);

COMMENT ON TABLE lesson_versions IS 'Immutable content snapshots. Every edit to a lesson plan creates a new version. This is the diff/restore source of truth.';

-- =============================================================
-- 7. lesson_activities  (individual activities within a procedure)
-- =============================================================
CREATE TABLE lesson_activities (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lesson_version_id     UUID NOT NULL REFERENCES lesson_versions(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  position              INT NOT NULL,                   -- ordering within the procedure
  activity_type         activity_type NOT NULL,
  title                 TEXT,
  description           TEXT NOT NULL,
  duration_minutes      INT,
  grouping              TEXT,                           -- 'whole_class' | 'small_group' | 'pairs' | 'individual'
  materials             TEXT[],
  teacher_actions       TEXT,
  student_actions       TEXT,
  differentiation_notes TEXT,                           -- SPED / multilingual adaptations
  ai_generated          BOOLEAN NOT NULL DEFAULT FALSE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_la_version ON lesson_activities(lesson_version_id, position) WHERE deleted_at IS NULL;
CREATE INDEX idx_la_tenant ON lesson_activities(tenant_id) WHERE deleted_at IS NULL;

-- =============================================================
-- 8. lesson_assessments  (assessment plan inside a lesson)
-- =============================================================
CREATE TABLE lesson_assessments (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lesson_version_id     UUID NOT NULL REFERENCES lesson_versions(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  assessment_type       TEXT NOT NULL,                  -- 'formative' | 'summative' | 'diagnostic'
  title                 TEXT NOT NULL,
  description           TEXT,
  total_points          NUMERIC(6,2),
  passing_score         NUMERIC(6,2),
  duration_minutes      INT,
  is_ai_generated       BOOLEAN NOT NULL DEFAULT FALSE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_lassess_version ON lesson_assessments(lesson_version_id) WHERE deleted_at IS NULL;

-- =============================================================
-- 9. lesson_resources  (files/links attached to a lesson)
-- =============================================================
CREATE TABLE lesson_resources (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lesson_version_id     UUID NOT NULL REFERENCES lesson_versions(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  resource_type         resource_type NOT NULL,
  title                 TEXT NOT NULL,
  description           TEXT,
  url                   TEXT,                           -- external URL or storage path
  document_id           UUID,                           -- FK to documents.documents (cross-schema)
  is_required           BOOLEAN NOT NULL DEFAULT FALSE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_lr_version ON lesson_resources(lesson_version_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lr_tenant ON lesson_resources(tenant_id) WHERE deleted_at IS NULL;

-- =============================================================
-- 10. lesson_approvals  (approval workflow log)
-- =============================================================
CREATE TABLE lesson_approvals (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lesson_plan_id        UUID NOT NULL REFERENCES lesson_plans(id) ON DELETE CASCADE,
  lesson_version_id     UUID NOT NULL REFERENCES lesson_versions(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  action                TEXT NOT NULL CHECK (action IN ('submit','approve','reject','request_changes','withdraw')),
  reviewer_user_id      UUID,                           -- NULL when action is 'submit' or 'withdraw'
  comments              TEXT,
  previous_status       lesson_status NOT NULL,
  new_status            lesson_status NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_lapp_plan ON lesson_approvals(lesson_plan_id);
CREATE INDEX idx_lapp_reviewer ON lesson_approvals(reviewer_user_id) WHERE reviewer_user_id IS NOT NULL;
-- Composite index for dashboard: "show approval timeline for this plan"
-- CREATE INDEX idx_lapp_plan_created ON lesson_approvals(lesson_plan_id, created_at DESC);
CREATE INDEX idx_lapp_created ON lesson_approvals(created_at DESC);

COMMENT ON TABLE lesson_approvals IS 'Append-only approval log. Used to render "who approved what when" and to compute approval-cycle time.';

-- =============================================================
-- 11. RLS
-- =============================================================
-- subjects: read public, write tenant admin
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE subjects FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_subjects_read ON subjects
  FOR SELECT USING (tenant_id IS NULL OR tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_subjects_write ON subjects
  FOR ALL USING (core.is_system_admin());

-- melcs: read public
ALTER TABLE melcs ENABLE ROW LEVEL SECURITY;
ALTER TABLE melcs FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_melcs_read ON melcs
  FOR SELECT USING (tenant_id IS NULL OR tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_melcs_write ON melcs
  FOR ALL USING (core.is_system_admin());

-- learning_competencies: read own tenant
ALTER TABLE learning_competencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_competencies FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_lc_read ON learning_competencies
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_lc_write ON learning_competencies
  FOR ALL USING (core.current_user_id() IS NOT NULL);

-- lesson_templates: read public + own tenant
ALTER TABLE lesson_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_templates FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_lt_read ON lesson_templates
  FOR SELECT USING (tenant_id IS NULL OR tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_lt_write ON lesson_templates
  FOR ALL USING (core.current_user_id() IS NOT NULL);

-- lesson_plans
ALTER TABLE lesson_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_plans FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_lp_read ON lesson_plans
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_lp_insert ON lesson_plans
  FOR INSERT WITH CHECK (tenant_id = core.current_tenant_id() AND core.current_user_id() IS NOT NULL);
CREATE POLICY rls_lp_update ON lesson_plans
  FOR UPDATE USING (
    tenant_id = core.current_tenant_id()
    AND (created_by = core.current_user_id() OR teacher_user_id = core.current_user_id() OR core.is_tenant_admin())
  );
CREATE POLICY rls_lp_delete ON lesson_plans
  FOR DELETE USING (core.is_tenant_admin() OR created_by = core.current_user_id());

-- lesson_versions
ALTER TABLE lesson_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_lv_read ON lesson_versions
  FOR SELECT USING (EXISTS (
    SELECT 1 FROM academic.lesson_plans lp
    WHERE lp.id = lesson_versions.lesson_plan_id
      AND (lp.tenant_id = core.current_tenant_id() OR core.is_system_admin())
  ));
CREATE POLICY rls_lv_write ON lesson_versions
  FOR ALL USING (core.current_user_id() IS NOT NULL);

-- lesson_activities, lesson_assessments, lesson_resources
ALTER TABLE lesson_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_activities FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_la_read ON lesson_activities
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_la_write ON lesson_activities
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE lesson_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_assessments FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_lassess_read ON lesson_assessments
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_lassess_write ON lesson_assessments
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE lesson_resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_resources FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_lr_read ON lesson_resources
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_lr_write ON lesson_resources
  FOR ALL USING (core.current_user_id() IS NOT NULL);

-- lesson_approvals
ALTER TABLE lesson_approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_approvals FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_lapp_read ON lesson_approvals
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_lapp_write ON lesson_approvals
  FOR ALL USING (core.current_user_id() IS NOT NULL);

-- =============================================================
-- 12. Triggers
-- =============================================================
DO $$
DECLARE
  t TEXT;
BEGIN
  FOR t IN
    SELECT unnest(ARRAY[
      'subjects', 'melcs', 'learning_competencies', 'lesson_templates',
      'lesson_plans', 'lesson_versions', 'lesson_activities',
      'lesson_assessments', 'lesson_resources', 'lesson_approvals'
    ])
  LOOP
    EXECUTE format('
      CREATE TRIGGER tg_set_updated_at
        BEFORE UPDATE ON academic.%I
        FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
    ', t);
  END LOOP;
END $$;

-- =============================================================
-- 13. Auto-create version snapshot on lesson_plan changes
-- =============================================================
-- This trigger creates a new lesson_version when a plan is first created.
-- Subsequent edits go through an explicit API that creates a new version
-- with proper diffing in the application layer.

CREATE OR REPLACE FUNCTION academic.tg_lesson_plan_create_v1() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.current_version_id IS NULL THEN
    INSERT INTO academic.lesson_versions
      (lesson_plan_id, version_number, created_by)
    VALUES (NEW.id, 1, NEW.created_by)
    RETURNING id INTO NEW.current_version_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_lesson_plan_create_v1
  BEFORE INSERT ON academic.lesson_plans
  FOR EACH ROW EXECUTE FUNCTION academic.tg_lesson_plan_create_v1();

-- =============================================================
-- 14. Add the now-resolvable circular FK
-- =============================================================
ALTER TABLE lesson_plans
  ADD CONSTRAINT fk_lesson_plans_current_version
  FOREIGN KEY (current_version_id) REFERENCES lesson_versions(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

-- =============================================================
-- End of Module 3
-- =============================================================
