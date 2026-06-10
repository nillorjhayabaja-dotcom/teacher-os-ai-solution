-- =============================================================
-- Module 6: DepEd School Forms Engine
-- Depends on: 01-auth-organization.sql, 02-student-information.sql
-- Tables: school_forms, school_form_templates, school_form_submissions,
--         school_form_versions, school_form_validations,
--         school_form_exports, school_form_signatures
-- Supported forms: SF1 (School Register), SF2 (Daily Attendance),
--                  SF5 (Promotion/Proficiency), SF9 (Progress Report),
--                  SF10 (Permanent Record)
-- =============================================================

CREATE SCHEMA IF NOT EXISTS forms;
SET search_path TO forms, sis, core, public;

-- =============================================================
-- ENUMS
-- =============================================================
CREATE TYPE school_form_code AS ENUM (
  'SF1', 'SF2', 'SF3', 'SF4', 'SF5', 'SF6', 'SF7', 'SF8', 'SF9', 'SF10',
  'NSBI', 'ALTERNATIVE_LEARNING', 'OTHER'
);

CREATE TYPE school_form_status AS ENUM (
  'draft', 'in_progress', 'pending_validation', 'pending_approval',
  'approved', 'rejected', 'submitted_to_deped', 'locked', 'archived'
);

CREATE TYPE validation_severity AS ENUM (
  'info', 'warning', 'error', 'blocker'
);

CREATE TYPE validation_rule_kind AS ENUM (
  'required', 'range', 'pattern', 'cross_field',
  'uniqueness', 'lookup', 'computation', 'custom'
);

CREATE TYPE export_format AS ENUM (
  'pdf', 'xlsx', 'csv', 'docx', 'json', 'xml', 'html'
);

-- =============================================================
-- 1. school_form_templates
-- =============================================================
CREATE TABLE school_form_templates (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,                           -- NULL for DepEd-issued
  form_code             school_form_code NOT NULL,
  version               TEXT NOT NULL,                  -- '2024-v1', '2023-v2'
  deped_version         TEXT,                           -- original DepEd version label
  is_official           BOOLEAN NOT NULL DEFAULT FALSE, -- true for DepEd-issued
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  title                 TEXT NOT NULL,
  description           TEXT,
  -- The form's structure: sections, fields, validations, layout
  schema_definition     JSONB NOT NULL,                  -- the JSON schema of the form
  field_definitions     JSONB NOT NULL,                  -- field-level metadata
  validation_rules      JSONB NOT NULL DEFAULT '[]',
  layout_definition     JSONB,                          -- PDF/print layout
  paper_size            TEXT DEFAULT 'A4',              -- 'A4' | 'legal' | 'letter' | 'long'
  orientation           TEXT DEFAULT 'portrait' CHECK (orientation IN ('portrait','landscape')),
  effective_from        DATE,
  effective_until       DATE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  UNIQUE (form_code, version)
);

CREATE INDEX idx_sft_form_code ON school_form_templates(form_code) WHERE deleted_at IS NULL;
CREATE INDEX idx_sft_active ON school_form_templates(is_active) WHERE is_active = TRUE AND deleted_at IS NULL;

COMMENT ON TABLE school_form_templates IS 'Versioned templates for each DepEd form. DepEd issues new versions; schools cannot modify official ones.';

-- =============================================================
-- 2. school_forms  (one row per form instance)
-- =============================================================
CREATE TABLE school_forms (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  school_year_id        UUID NOT NULL,
  template_id           UUID NOT NULL REFERENCES school_form_templates(id) ON DELETE RESTRICT,
  form_code             school_form_code NOT NULL,      -- denormalized for fast queries
  version               TEXT NOT NULL,                  -- denormalized
  -- The scope of this form instance
  grade_level           INT,
  section_id            UUID,                           -- for SF1, SF2, etc.
  student_id            UUID,                           -- for SF9, SF10 (per-student forms)
  quarter               INT,                            -- for SF2 (per quarter)
  month                 INT,                            -- for SF2 (monthly attendance)
  -- Status & workflow
  status                school_form_status NOT NULL DEFAULT 'draft',
  -- The actual form data
  form_data             JSONB NOT NULL DEFAULT '{}'::jsonb,
  -- Validation
  validation_passed     BOOLEAN NOT NULL DEFAULT FALSE,
  validation_errors     JSONB NOT NULL DEFAULT '[]',     -- summary of latest validation run
  last_validated_at     TIMESTAMPTZ,
  -- Submission & approval
  submitted_at          TIMESTAMPTZ,
  submitted_by          UUID,
  approved_at           TIMESTAMPTZ,
  approved_by           UUID,
  rejected_at           TIMESTAMPTZ,
  rejected_by           UUID,
  rejection_reason      TEXT,
  -- Locking
  locked_at             TIMESTAMPTZ,                    -- when submitted to DepEd, locked
  locked_by             UUID,
  -- Counts
  current_version       INT NOT NULL DEFAULT 1,
  export_count          INT NOT NULL DEFAULT 0,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_sf_tenant ON school_forms(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sf_template ON school_forms(template_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sf_code ON school_forms(tenant_id, form_code) WHERE deleted_at IS NULL;
CREATE INDEX idx_sf_sy ON school_forms(tenant_id, school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sf_section ON school_forms(section_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sf_student ON school_forms(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sf_status ON school_forms(tenant_id, status) WHERE deleted_at IS NULL;
-- Issue 10 fix: composite index for SF2 generation queries
CREATE INDEX idx_sf_formcode_section_quarter ON school_forms(form_code, section_id, quarter) WHERE deleted_at IS NULL;
CREATE INDEX idx_sf_data_gin ON school_forms USING gin (form_data) WHERE deleted_at IS NULL;

-- =============================================================
-- 3. school_form_versions  (immutable snapshot history)
-- =============================================================
CREATE TABLE school_form_versions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  school_form_id        UUID NOT NULL REFERENCES school_forms(id) ON DELETE CASCADE,
  version_number        INT NOT NULL,
  form_data_snapshot    JSONB NOT NULL,
  validation_state      JSONB,
  change_summary        TEXT,
  created_by            UUID NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (school_form_id, version_number)
);

CREATE INDEX idx_sfv_form ON school_form_versions(school_form_id);

-- =============================================================
-- 4. school_form_validations  (validation log)
-- =============================================================
CREATE TABLE school_form_validations (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  school_form_id        UUID NOT NULL REFERENCES school_forms(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  rule_id               TEXT,                           -- the rule's id from the template
  rule_kind             validation_rule_kind NOT NULL,
  severity              validation_severity NOT NULL,
  field_path            TEXT,                           -- e.g., 'students[3].lrn'
  message               TEXT NOT NULL,
  actual_value          JSONB,
  expected              JSONB,
  is_resolved           BOOLEAN NOT NULL DEFAULT FALSE,
  resolved_at           TIMESTAMPTZ,
  resolved_by           UUID,
  resolution_note       TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_sfv_form ON school_form_validations(school_form_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sfv_unresolved ON school_form_validations(school_form_id)
  WHERE is_resolved = FALSE AND severity IN ('error','blocker') AND deleted_at IS NULL;
CREATE INDEX idx_sfv_severity ON school_form_validations(tenant_id, severity) WHERE deleted_at IS NULL;

-- =============================================================
-- 5. school_form_exports  (every export is logged for audit)
-- =============================================================
CREATE TABLE school_form_exports (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  school_form_id        UUID NOT NULL REFERENCES school_forms(id) ON DELETE RESTRICT,
  tenant_id             UUID NOT NULL,
  export_format         export_format NOT NULL,
  file_url              TEXT,                           -- S3 / Supabase Storage path
  file_size_bytes       BIGINT,
  file_hash             TEXT,                           -- sha256 for integrity
  purpose               TEXT,                           -- 'deped_submission' | 'parent_copy' | 'archive' | 'print'
  exported_by           UUID NOT NULL,
  exported_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at            TIMESTAMPTZ,                    -- for time-limited signed URLs
  download_count        INT NOT NULL DEFAULT 0,
  last_downloaded_at    TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_sfe_form ON school_form_exports(school_form_id);
CREATE INDEX idx_sfe_tenant_recent ON school_form_exports(tenant_id, exported_at DESC);
CREATE INDEX idx_sfe_purpose ON school_form_exports(tenant_id, purpose) WHERE deleted_at IS NULL;

-- =============================================================
-- 6. school_form_signatures  (digital signatures for approval)
-- =============================================================
CREATE TABLE school_form_signatures (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  school_form_id        UUID NOT NULL REFERENCES school_forms(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  signer_user_id        UUID NOT NULL,
  signer_role           TEXT NOT NULL,                  -- 'class_teacher' | 'school_head' | 'district_rep'
  signature_image_url   TEXT,                           -- drawn/typed signature
  signature_data_hash   TEXT NOT NULL,                  -- hash of the signed content
  signed_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  ip_address            INET,
  user_agent            TEXT,
  revoked_at            TIMESTAMPTZ,
  revoked_by            UUID,
  revocation_reason     TEXT,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_sfs_form ON school_form_signatures(school_form_id);
CREATE INDEX idx_sfs_signer ON school_form_signatures(signer_user_id);

-- =============================================================
-- 7. school_form_field_values  (optional normalized form of data)
-- (Useful for fast per-field queries when JSONB is too slow)
-- =============================================================
CREATE TABLE school_form_field_values (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  school_form_id        UUID NOT NULL REFERENCES school_forms(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  field_path            TEXT NOT NULL,                  -- 'students[3].lrn'
  value_text            TEXT,
  value_numeric         NUMERIC,
  value_date            DATE,
  value_boolean         BOOLEAN,
  value_json            JSONB,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (school_form_id, field_path)
);

CREATE INDEX idx_sffv_form ON school_form_field_values(school_form_id);
CREATE INDEX idx_sffv_path ON school_form_field_values(school_form_id, field_path);
CREATE INDEX idx_sffv_text ON school_form_field_values(value_text) WHERE value_text IS NOT NULL;
CREATE INDEX idx_sffv_numeric ON school_form_field_values(value_numeric) WHERE value_numeric IS NOT NULL;

-- =============================================================
-- 8. RLS
-- =============================================================
ALTER TABLE school_form_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_form_templates FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_sft_read ON school_form_templates
  FOR SELECT USING (tenant_id IS NULL OR tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_sft_write ON school_form_templates
  FOR ALL USING (core.is_system_admin() OR (tenant_id = core.current_tenant_id() AND NOT is_official));

ALTER TABLE school_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_forms FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_sf_read ON school_forms
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_sf_write ON school_forms
  FOR ALL USING (tenant_id = core.current_tenant_id() AND (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL));

ALTER TABLE school_form_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_form_versions FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_sfv_read ON school_form_versions
  FOR SELECT USING (EXISTS (
    SELECT 1 FROM forms.school_forms sf
    WHERE sf.id = school_form_versions.school_form_id
      AND (sf.tenant_id = core.current_tenant_id() OR core.is_system_admin())
  ));
CREATE POLICY rls_sfv_write ON school_form_versions
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE school_form_validations ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_form_validations FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_sfv2_read ON school_form_validations
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_sfv2_write ON school_form_validations
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE school_form_exports ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_form_exports FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_sfe_read ON school_form_exports
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_sfe_write ON school_form_exports
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE school_form_signatures ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_form_signatures FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_sfs_read ON school_form_signatures
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_sfs_write ON school_form_signatures
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE school_form_field_values ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_form_field_values FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_sffv_read ON school_form_field_values
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_sffv_write ON school_form_field_values
  FOR ALL USING (core.current_user_id() IS NOT NULL);

-- =============================================================
-- 9. Triggers
-- =============================================================
DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'school_form_templates', 'school_forms', 'school_form_versions',
    'school_form_validations', 'school_form_exports',
    'school_form_signatures', 'school_form_field_values'
  ])
  LOOP
    EXECUTE format('
      CREATE TRIGGER tg_set_updated_at BEFORE UPDATE ON forms.%I
        FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
    ', t);
  END LOOP;
END $$;

-- =============================================================
-- 10. Lock on submitted-to-DepEd forms
-- =============================================================
CREATE OR REPLACE FUNCTION forms.tg_lock_submitted_form() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'submitted_to_deped' AND (OLD.status IS NULL OR OLD.status <> 'submitted_to_deped') THEN
    NEW.locked_at := now();
    NEW.locked_by := NEW.submitted_by;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_lock_submitted_form
  BEFORE UPDATE ON forms.school_forms
  FOR EACH ROW EXECUTE FUNCTION forms.tg_lock_submitted_form();

-- =============================================================
-- 11. Prevent edits to locked forms
-- =============================================================
CREATE OR REPLACE FUNCTION forms.tg_prevent_locked_edit() RETURNS TRIGGER AS $$
BEGIN
  IF OLD.locked_at IS NOT NULL THEN
    RAISE EXCEPTION 'Cannot edit form % — it has been submitted to DepEd and is locked', OLD.id
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_prevent_locked_edit
  BEFORE UPDATE ON forms.school_forms
  FOR EACH ROW EXECUTE FUNCTION forms.tg_prevent_locked_edit();

-- =============================================================
-- End of Module 6
-- =============================================================
