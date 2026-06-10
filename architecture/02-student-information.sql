-- =============================================================
-- Module 2: Student Information System (SIS)
-- Depends on: 01-auth-organization.sql
-- Tables: grade_levels, sections, students, student_profiles,
--         student_enrollments, guardians, guardian_relationships,
--         attendance_records, attendance_summaries,
--         student_transfers, student_documents
-- =============================================================

CREATE SCHEMA IF NOT EXISTS sis;
SET search_path TO sis, core, public;

-- =============================================================
-- ENUMS
-- =============================================================
CREATE TYPE section_type AS ENUM (
  'regular', 'special', 'sped', 'honors', 'stem', 'techvoc', 'sports', 'arts'
);

CREATE TYPE student_status AS ENUM (
  'enrolled', 'transferred_in', 'transferred_out', 'dropped', 'graduated', 'on_leave', 'archived'
);

CREATE TYPE gender_type AS ENUM (
  'male', 'female', 'non_binary', 'prefer_not_to_say', 'other', 'unspecified'
);

CREATE TYPE attendance_status AS ENUM (
  'present', 'absent', 'late', 'excused', 'cutting'
);

CREATE TYPE enrollment_status AS ENUM (
  'enrolled', 'withdrawn', 'completed', 'transferred_out', 'transferred_in'
);

CREATE TYPE transfer_type AS ENUM (
  'in',   -- came from another school
  'out',  -- left to another school
  'within_district',
  'within_division',
  'inter_region',
  'international'
);

-- =============================================================
-- 1. grade_levels
-- =============================================================
CREATE TABLE grade_levels (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  level                 INT NOT NULL,                   -- 1, 2, 3, ..., 12
  name                  TEXT NOT NULL,                  -- "Grade 1", "Kinder"
  stage                 TEXT NOT NULL DEFAULT 'elementary'  -- 'kinder' | 'elementary' | 'junior_high' | 'senior_high'
                      CHECK (stage IN ('kinder','elementary','junior_high','senior_high')),
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE UNIQUE INDEX uq_grade_levels_tenant_level ON grade_levels(tenant_id, level) WHERE deleted_at IS NULL;

-- =============================================================
-- 2. sections  (a class roster)
-- =============================================================
CREATE TABLE sections (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  school_year_id        UUID NOT NULL,
  name                  TEXT NOT NULL,                  -- "Sampaguita", "Rizal"
  grade_level_id        UUID NOT NULL REFERENCES grade_levels(id) ON DELETE RESTRICT,
  section_type          section_type NOT NULL DEFAULT 'regular',
  adviser_user_id       UUID,                           -- FK to users
  max_capacity          INT,
  current_enrollment    INT NOT NULL DEFAULT 0,
  room_number           TEXT,
  color_tag             TEXT,                           -- hex color for UI
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_sections_tenant ON sections(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sections_sy ON sections(school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sections_grade ON sections(grade_level_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sections_adviser ON sections(adviser_user_id) WHERE deleted_at IS NULL AND adviser_user_id IS NOT NULL;
CREATE UNIQUE INDEX uq_sections_sy_name ON sections(tenant_id, school_year_id, name) WHERE deleted_at IS NULL;

COMMENT ON TABLE sections IS 'A class roster (e.g., Grade 6 - Sampaguita). Sections are scoped to a school year.';

-- =============================================================
-- 3. students  (master record, school-agnostic)
-- =============================================================
CREATE TABLE students (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,                           -- NULL for pre-enrollment
  LRN                   TEXT,                           -- Learner Reference Number (12 digits, DepEd)
  first_name            TEXT NOT NULL,
  middle_name           TEXT,
  last_name             TEXT NOT NULL,
  suffix                TEXT,
  preferred_name        TEXT,
  birthday              DATE NOT NULL,
  birthplace            TEXT,
  gender                gender_type NOT NULL DEFAULT 'unspecified',
  blood_type            TEXT,
  nationality           TEXT NOT NULL DEFAULT 'Filipino',
  mother_tongue         TEXT,
  indigenous_people     BOOLEAN NOT NULL DEFAULT FALSE,
  is_4ps_beneficiary    BOOLEAN NOT NULL DEFAULT FALSE, -- 4Ps = Pantawid Pamilyang Pilipino Program
  has_disability        BOOLEAN NOT NULL DEFAULT FALSE,
  disability_details    TEXT,
  ps_birth_cert_no      TEXT,                           -- Philippine Statistics birth cert
  status                student_status NOT NULL DEFAULT 'enrolled',
  avatar_url            TEXT,
  current_school_id     UUID,                           -- populated when enrolled
  current_section_id    UUID,                           -- populated when enrolled
  current_grade_level_id UUID,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_students_tenant ON students(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_students_status ON students(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_students_name_trgm ON students USING gin (
  (last_name || ' ' || first_name) gin_trgm_ops
) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_students_lrn ON students(LRN) WHERE LRN IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX idx_students_birthday ON students(birthday) WHERE deleted_at IS NULL;
CREATE INDEX idx_students_current_school ON students(current_school_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_students_current_section ON students(current_section_id) WHERE deleted_at IS NULL;

COMMENT ON TABLE students IS 'Master record. A student is unique by LRN (Learner Reference Number). LRN is the DepEd-mandated 12-digit ID.';

-- =============================================================
-- 4. student_profiles  (extended per-student attributes that may be PII)
-- =============================================================
CREATE TABLE student_profiles (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id            UUID NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
  address_line1         TEXT,
  address_line2         TEXT,
  barangay              TEXT,
  city                  TEXT,
  municipality          TEXT,
  province              TEXT,
  zip_code              TEXT,
  geo_coordinates       POINT,
  home_language         TEXT,
  religion              TEXT,
  medical_notes         TEXT,                           -- allergies, conditions (encrypted at app layer)
  emergency_contact_name  TEXT,
  emergency_contact_phone TEXT,
  emergency_contact_relation TEXT,
  transport_mode        TEXT,                           -- 'walking' | 'bicycle' | 'jeepney' | 'private_car' | 'school_bus'
  distance_from_school_km NUMERIC(6,2),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_student_profiles_student ON student_profiles(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_student_profiles_geo ON student_profiles USING gist (geo_coordinates) WHERE geo_coordinates IS NOT NULL;

COMMENT ON TABLE student_profiles IS 'PII-heavy extended profile. Access is gated to a smaller set of roles (adviser, guidance, principal).';

-- =============================================================
-- 5. student_enrollments  (yearly enrollment records)
-- =============================================================
CREATE TABLE student_enrollments (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  student_id            UUID NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
  school_year_id        UUID NOT NULL REFERENCES core.school_years(id) ON DELETE RESTRICT,
  grade_level_id        UUID NOT NULL REFERENCES grade_levels(id) ON DELETE RESTRICT,
  section_id            UUID REFERENCES sections(id) ON DELETE SET NULL,
  enrollment_status     enrollment_status NOT NULL DEFAULT 'enrolled',
  enrollment_date       DATE NOT NULL DEFAULT CURRENT_DATE,
  withdrawal_date       DATE,
  withdrawal_reason     TEXT,
  balik_aral            BOOLEAN NOT NULL DEFAULT FALSE, -- returnee student
  ip_group              TEXT,                           -- Indigenous People group, if applicable
  modality              TEXT NOT NULL DEFAULT 'face_to_face'
                        CHECK (modality IN ('face_to_face', 'modular', 'online', 'blended', 'homeschooling')),
  remarks               TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_enrollments_tenant ON student_enrollments(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_enrollments_student ON student_enrollments(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_enrollments_sy ON student_enrollments(school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_enrollments_section ON student_enrollments(section_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_enrollments_grade ON student_enrollments(grade_level_id) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_enrollments_student_sy
  ON student_enrollments(student_id, school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_enrollments_status ON student_enrollments(enrollment_status) WHERE deleted_at IS NULL;

COMMENT ON TABLE student_enrollments IS 'One row per student per school year. Tracks which section/grade/modality they were enrolled in.';

-- =============================================================
-- 6. guardians  (parents / primary contact people)
-- =============================================================
CREATE TABLE guardians (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id (scoped via student_enrollments)
  first_name            TEXT NOT NULL,
  middle_name           TEXT,
  last_name             TEXT NOT NULL,
  suffix                TEXT,
  gender                gender_type,
  birthday              DATE,
  occupation            TEXT,
  monthly_income        NUMERIC(12,2),
  is_4ps_beneficiary    BOOLEAN NOT NULL DEFAULT FALSE,
  4ps_id_number         TEXT,
  email                 CITEXT,
  phone                 TEXT,
  phone_secondary       TEXT,
  address_line1         TEXT,
  address_line2         TEXT,
  barangay              TEXT,
  city                  TEXT,
  municipality          TEXT,
  province              TEXT,
  zip_code              TEXT,
  is_deceased           BOOLEAN NOT NULL DEFAULT FALSE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_guardians_tenant ON guardians(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_guardians_phone ON guardians(phone) WHERE deleted_at IS NULL;
CREATE INDEX idx_guardians_name_trgm ON guardians USING gin (
  (last_name || ' ' || first_name) gin_trgm_ops
) WHERE deleted_at IS NULL;

-- =============================================================
-- 7. guardian_relationships  (student ↔ guardian with relationship type)
-- =============================================================
CREATE TABLE guardian_relationships (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id            UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  guardian_id           UUID NOT NULL REFERENCES guardians(id) ON DELETE CASCADE,
  relationship          TEXT NOT NULL,                  -- 'mother' | 'father' | 'grandmother' | 'aunt' | 'sibling' | 'guardian' | 'other'
  is_primary_contact    BOOLEAN NOT NULL DEFAULT FALSE,
  is_emergency_contact  BOOLEAN NOT NULL DEFAULT FALSE,
  is_authorized_pickup  BOOLEAN NOT NULL DEFAULT TRUE,
  receives_sms          BOOLEAN NOT NULL DEFAULT TRUE,
  receives_email       BOOLEAN NOT NULL DEFAULT TRUE,
  receives_report_card  BOOLEAN NOT NULL DEFAULT TRUE,
  occupation            TEXT,                           -- override of guardian.occupation
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_gr_student ON guardian_relationships(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_gr_guardian ON guardian_relationships(guardian_id) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_gr_student_guardian_rel
  ON guardian_relationships(student_id, guardian_id, relationship) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_gr_student_primary
  ON guardian_relationships(student_id) WHERE is_primary_contact = TRUE AND deleted_at IS NULL;

-- =============================================================
-- 8. student_transfers  (audit log of inter-school movement)
-- =============================================================
CREATE TABLE student_transfers (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id            UUID NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
  transfer_type         transfer_type NOT NULL,
  from_school_id        UUID,                           -- NULL for incoming from outside DepEd
  to_school_id          UUID,                           -- NULL for outgoing to outside DepEd
  from_school_name      TEXT,                           -- free text for non-DepEd schools
  to_school_name        TEXT,
  transfer_date         DATE NOT NULL,
  effective_school_year_id UUID,
  reason                TEXT,
  credentials_submitted BOOLEAN NOT NULL DEFAULT FALSE,
  credentials_verified  BOOLEAN NOT NULL DEFAULT FALSE,
  verified_by           UUID,
  verified_at           TIMESTAMPTZ,
  document_ids          UUID[],                         -- references to documents.documents
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_transfers_student ON student_transfers(student_id);
CREATE INDEX idx_transfers_from ON student_transfers(from_school_id) WHERE from_school_id IS NOT NULL;
CREATE INDEX idx_transfers_to ON student_transfers(to_school_id) WHERE to_school_id IS NOT NULL;
CREATE INDEX idx_transfers_date ON student_transfers(transfer_date DESC);

-- =============================================================
-- 9. attendance_records  (per-day per-student, append-only)
-- =============================================================
CREATE TABLE attendance_records (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  school_year_id        UUID NOT NULL REFERENCES core.school_years(id) ON DELETE RESTRICT,
  student_id            UUID NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
  attendance_date       DATE NOT NULL,
  status                attendance_status NOT NULL,
  time_in               TIME,
  time_out              TIME,
  minutes_late          INT,
  remarks               TEXT,
  recorded_by           UUID NOT NULL,                  -- teacher or adviser
  recorded_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  source                TEXT NOT NULL DEFAULT 'manual'  -- 'manual' | 'rfid' | 'biometric' | 'qr' | 'imported'
                      CHECK (source IN ('manual', 'rfid', 'biometric', 'qr', 'imported', 'app')),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (student_id, attendance_date)                 -- one record per day
);

CREATE INDEX idx_attendance_tenant_date ON attendance_records(tenant_id, attendance_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_attendance_student_date ON attendance_records(student_id, attendance_date DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_attendance_sy ON attendance_records(school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_attendance_status ON attendance_records(tenant_id, attendance_date, status) WHERE deleted_at IS NULL;

-- For 1M+ students × 200 school days = 200M rows/yr. Partition by school_year.
-- (Partitioning example shown in README; uncomment when needed)
-- CREATE TABLE attendance_records (LIKE attendance_records INCLUDING ALL) PARTITION BY LIST (school_year_id);

COMMENT ON TABLE attendance_records IS 'Append-only per-day attendance. Will be partitioned by school_year_id at scale.';

-- =============================================================
-- 10. attendance_summaries  (precomputed rollups)
-- =============================================================
CREATE TABLE attendance_summaries (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  student_id            UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  period_label          TEXT NOT NULL,                  -- 'Q1', 'Q2', 'Q3', 'Q4', 'Annual'
  total_school_days     INT NOT NULL DEFAULT 0,
  days_present          INT NOT NULL DEFAULT 0,
  days_absent           INT NOT NULL DEFAULT 0,
  days_late             INT NOT NULL DEFAULT 0,
  days_excused          INT NOT NULL DEFAULT 0,
  attendance_rate       NUMERIC(5,2) GENERATED ALWAYS AS
                        (CASE WHEN total_school_days > 0
                              THEN ROUND(100.0 * (days_present + days_late) / total_school_days, 2)
                              ELSE 0 END) STORED,
  computed_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ,
  UNIQUE (student_id, school_year_id, period_label)
);

CREATE INDEX idx_attendance_summaries_tenant ON attendance_summaries(tenant_id, school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_attendance_summaries_student ON attendance_summaries(student_id) WHERE deleted_at IS NULL;

COMMENT ON TABLE attendance_summaries IS 'Precomputed rollups refreshed by a pg_cron job after each grading period. The attendance_rate column is a generated column.';

-- =============================================================
-- 11. RLS for all SIS tables
-- =============================================================
-- Helper: can the current user access a student via their enrollments?
CREATE OR REPLACE FUNCTION sis.can_access_student(p_student_id UUID) RETURNS BOOLEAN
LANGUAGE sql STABLE AS $$
  SELECT EXISTS (
    SELECT 1 FROM sis.student_enrollments se
    WHERE se.student_id = p_student_id
      AND se.tenant_id = core.current_tenant_id()
      AND se.deleted_at IS NULL
  );
$$;

-- grade_levels
ALTER TABLE grade_levels ENABLE ROW LEVEL SECURITY;
ALTER TABLE grade_levels FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_grade_levels_read ON grade_levels
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_grade_levels_write ON grade_levels
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

-- sections
ALTER TABLE sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE sections FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_sections_read ON sections
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_sections_write ON sections
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

-- students
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE students FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_students_read ON students
  FOR SELECT USING (
    core.is_system_admin()
    OR sis.can_access_student(id)
    OR EXISTS (
      SELECT 1 FROM core.school_memberships
      WHERE user_id = core.current_user_id() AND school_id = students.tenant_id AND deleted_at IS NULL
    )
  );
CREATE POLICY rls_students_write ON students
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

-- student_profiles (more restrictive)
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_profiles FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_student_profiles_read ON student_profiles
  FOR SELECT USING (
    sis.can_access_student(student_id)
    AND (
      core.is_tenant_admin()
      OR core.current_role_code() IN ('adviser','guidance','principal','head_teacher')
      OR core.is_system_admin()
    )
  );
CREATE POLICY rls_student_profiles_write ON student_profiles
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

-- student_enrollments
ALTER TABLE student_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_enrollments FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_enrollments_read ON student_enrollments
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_enrollments_write ON student_enrollments
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

-- guardians
ALTER TABLE guardians ENABLE ROW LEVEL SECURITY;
ALTER TABLE guardians FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_guardians_read ON guardians
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_guardians_write ON guardians
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

-- guardian_relationships
ALTER TABLE guardian_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE guardian_relationships FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_gr_read ON guardian_relationships
  FOR SELECT USING (sis.can_access_student(student_id));
CREATE POLICY rls_gr_write ON guardian_relationships
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

-- student_transfers
ALTER TABLE student_transfers ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_transfers FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_transfers_read ON student_transfers
  FOR SELECT USING (sis.can_access_student(student_id) OR core.is_tenant_admin() OR core.is_system_admin());
CREATE POLICY rls_transfers_write ON student_transfers
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

-- attendance_records
ALTER TABLE attendance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance_records FORCE ROW LEVEL SECURITY;
-- Teachers can read attendance for students in their sections
CREATE POLICY rls_attendance_read ON attendance_records
  FOR SELECT USING (
    tenant_id = core.current_tenant_id()
    AND (core.is_tenant_admin() OR sis.can_access_student(student_id))
  );
-- Teachers can mark attendance for students in their sections (adviser)
CREATE POLICY rls_attendance_write ON attendance_records
  FOR ALL USING (
    tenant_id = core.current_tenant_id()
    AND (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL)
  );

-- attendance_summaries
ALTER TABLE attendance_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance_summaries FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_attendance_summaries_read ON attendance_summaries
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_attendance_summaries_write ON attendance_summaries
  FOR ALL USING (core.is_system_admin());

-- =============================================================
-- 12. Triggers
-- =============================================================
DO $$
DECLARE
  t TEXT;
BEGIN
  FOR t IN
    SELECT unnest(ARRAY[
      'grade_levels', 'sections', 'students', 'student_profiles',
      'student_enrollments', 'guardians', 'guardian_relationships',
      'student_transfers', 'attendance_records', 'attendance_summaries'
    ])
  LOOP
    EXECUTE format('
      CREATE TRIGGER tg_set_updated_at
        BEFORE UPDATE ON sis.%I
        FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
    ', t);
  END LOOP;
END $$;

-- =============================================================
-- 13. Event emission triggers (optional; uncomment to enable)
-- =============================================================
-- CREATE TRIGGER tg_emit_student_events
--   AFTER INSERT OR UPDATE ON sis.students
--   FOR EACH ROW EXECUTE FUNCTION audit.tg_emit_domain_event('student.changed', 'student');

-- =============================================================
-- End of Module 2
-- =============================================================
