-- =============================================================
-- Module 1: Authentication & Organization
-- Depends on: pgcrypto, uuid-ossp (Supabase provides these)
-- Tables: organizations, schools, school_years, users,
--         user_profiles, roles, permissions, user_role_assignments,
--         organization_members, school_memberships
-- =============================================================

CREATE SCHEMA IF NOT EXISTS core;
SET search_path TO core, public;

-- ---------- Extensions ----------
CREATE EXTENSION IF NOT EXISTS pgcrypto;      -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS citext;        -- case-insensitive email
CREATE EXTENSION IF NOT EXISTS btree_gist;    -- exclusion constraints

-- =============================================================
-- ENUMS
-- =============================================================
CREATE TYPE organization_type AS ENUM (
  'deped_central',     -- DepEd Central Office
  'region',            -- DepEd Regional Office
  'division',          -- Division Office (cluster of schools)
  'district',          -- District (cluster of schools within a division)
  'school',            -- Individual school
  'individual'         -- Solo teacher account (premium)
);

CREATE TYPE school_type AS ENUM (
  'elementary',
  'integrated',         -- K-12
  'junior_high',
  'senior_high',
  'kinder_plus',
  'sped_center'
);

CREATE TYPE school_classification AS ENUM (
  'small',              -- < 200 students
  'medium',             -- 200-500
  'large',              -- 500-1000
  'mega'                -- > 1000
);

CREATE TYPE school_year_status AS ENUM (
  'planning',           -- before SY starts
  'active',             -- current SY
  'closing',            -- end-of-year processing
  'archived'            -- historical
);

CREATE TYPE user_status AS ENUM (
  'invited',            -- invitation sent, not yet accepted
  'active',
  'suspended',
  'deactivated',
  'archived'
);

CREATE TYPE assignment_status AS ENUM (
  'active',
  'inactive',
  'pending_start',
  'expired'
);

-- =============================================================
-- Helper trigger function (used by every domain table)
-- =============================================================
CREATE OR REPLACE FUNCTION core.tg_set_updated_at() RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================
-- 1. organizations  (top of the tenant hierarchy)
-- =============================================================
CREATE TABLE organizations (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type                  organization_type NOT NULL,
  name                  TEXT NOT NULL,
  code                  TEXT,                           -- e.g., DepEd Region IV-A CALABARZON
  parent_organization_id UUID REFERENCES organizations(id) ON DELETE RESTRICT,
  region_code           TEXT,                           -- e.g., "IV-A"
  division_code         TEXT,                           -- e.g., "Cavite"
  district_code         TEXT,
  address_line1         TEXT,
  address_line2         TEXT,
  city                  TEXT,
  province              TEXT,
  zip_code              TEXT,
  country               TEXT NOT NULL DEFAULT 'PH',
  phone                 TEXT,
  email                 CITEXT,
  website_url           TEXT,
  logo_url              TEXT,
  settings              JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  activated_at          TIMESTAMPTZ,
  deactivated_at        TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_organizations_parent_id ON organizations(parent_organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_type ON organizations(type) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_organizations_code ON organizations(code) WHERE code IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX idx_organizations_name_trgm ON organizations USING gin (name gin_trgm_ops);

COMMENT ON TABLE organizations IS 'Hierarchy: DepEd Central > Region > Division > District > School. Every tenant maps to one row.';

-- =============================================================
-- 2. schools
-- =============================================================
CREATE TABLE schools (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
  school_id             TEXT NOT NULL,                  -- DepEd school ID (e.g., 301234)
  name                  TEXT NOT NULL,
  school_type           school_type NOT NULL,
  classification        school_classification,
  grade_levels_offered  INT[] NOT NULL DEFAULT '{}',     -- e.g., {1,2,3,4,5,6} for elementary
  curriculum             TEXT NOT NULL DEFAULT 'K-12',
  address_line1         TEXT,
  address_line2         TEXT,
  city                  TEXT,
  municipality          TEXT,
  province              TEXT,
  zip_code              TEXT,
  region                TEXT,
  division              TEXT,
  district              TEXT,
  barangay              TEXT,
  geo_coordinates       POINT,
  phone                 TEXT,
  email                 CITEXT,
  website_url           TEXT,
  logo_url              TEXT,
  principal_name        TEXT,
  total_enrollment      INT,
  school_head_user_id   UUID,                           -- FK added in ALTER TABLE block at end of module
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  activated_at          TIMESTAMPTZ,
  deactivated_at        TIMESTAMPTZ,
  settings              JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_schools_organization_id ON schools(organization_id) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_schools_school_id ON schools(school_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_schools_name_trgm ON schools USING gin (name gin_trgm_ops);
CREATE INDEX idx_schools_geo ON schools USING gist (geo_coordinates) WHERE geo_coordinates IS NOT NULL;
CREATE INDEX idx_schools_active ON schools(is_active) WHERE deleted_at IS NULL AND is_active = TRUE;

COMMENT ON TABLE schools IS 'Individual schools. The most common tenant_id for school-scoped data.';

-- =============================================================
-- 3. school_years
-- =============================================================
CREATE TABLE school_years (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id or org_id
  label                 TEXT NOT NULL,                  -- e.g., "S.Y. 2025-2026"
  start_date            DATE NOT NULL,
  end_date              DATE NOT NULL,
  status                school_year_status NOT NULL DEFAULT 'planning',
  is_current            BOOLEAN NOT NULL DEFAULT FALSE,
  grading_periods       JSONB NOT NULL DEFAULT '[]',    -- [{"name":"Q1","start":"...","end":"..."}]
  activated_at          TIMESTAMPTZ,
  closed_at             TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
  CHECK (end_date > start_date)
);

CREATE INDEX idx_school_years_tenant ON school_years(tenant_id) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_school_years_label_per_tenant ON school_years(tenant_id, label) WHERE deleted_at IS NULL;
-- Only one current school year per tenant
CREATE UNIQUE INDEX uq_school_years_current_per_tenant
  ON school_years(tenant_id) WHERE is_current = TRUE AND deleted_at IS NULL;

COMMENT ON TABLE school_years IS 'Each school year is a workspace boundary. Q1, Q2, Q3, Q4 all roll up to one SY.';

-- =============================================================
-- 4. users (1:1 with auth.users in Supabase)
-- =============================================================
CREATE TABLE users (
  id                    UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  -- auth.users is Supabase's built-in. For non-Supabase, the FK is omitted.
  email                 CITEXT NOT NULL,
  phone                 TEXT,
  email_verified        BOOLEAN NOT NULL DEFAULT FALSE,
  phone_verified        BOOLEAN NOT NULL DEFAULT FALSE,
  status                user_status NOT NULL DEFAULT 'invited',
  is_super_admin        BOOLEAN NOT NULL DEFAULT FALSE, -- platform owner (DepEd sysadmin)
  last_sign_in_at       TIMESTAMPTZ,
  last_active_at        TIMESTAMPTZ,
  mfa_enabled           BOOLEAN NOT NULL DEFAULT FALSE,
  locale                TEXT NOT NULL DEFAULT 'en-PH',
  timezone              TEXT NOT NULL DEFAULT 'Asia/Manila',
  preferences           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE UNIQUE INDEX uq_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_status ON users(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_last_active ON users(last_active_at DESC) WHERE deleted_at IS NULL;

COMMENT ON TABLE users IS 'Profile mirror of Supabase auth.users. Holds app-level concerns (status, locale, MFA, etc.).';

-- =============================================================
-- 5. user_profiles  (per-user personal details)
-- =============================================================
CREATE TABLE user_profiles (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  first_name            TEXT NOT NULL,
  middle_name           TEXT,
  last_name             TEXT NOT NULL,
  suffix                TEXT,                           -- Jr., III, etc.
  preferred_name        TEXT,
  avatar_url            TEXT,
  birthday              DATE,
  gender                TEXT,                           -- 'male' | 'female' | 'prefer_not_to_say' | 'other'
  civil_status          TEXT,
  address_line1         TEXT,
  address_line2         TEXT,
  city                  TEXT,
  province              TEXT,
  zip_code              TEXT,
  employee_id           TEXT,                           -- DepEd employee number
  position_title        TEXT,                           -- Teacher I, II, III, Master Teacher, Head Teacher
  PRC_license_no        TEXT,                           -- PRC license (for master teachers)
  plantilla_number      TEXT,
  date_hired            DATE,
  highest_degree        TEXT,                           -- Bachelor's, Master's, Doctorate
  major_specialization  TEXT,
  bio                  TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_profiles_name_trgm ON user_profiles USING gin (
  (first_name || ' ' || last_name) gin_trgm_ops
) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_profiles_employee_id ON user_profiles(employee_id) WHERE employee_id IS NOT NULL AND deleted_at IS NULL;

COMMENT ON TABLE user_profiles IS 'Personal & employment details. Separate from users to keep auth table lean.';

-- =============================================================
-- 6. roles  (per-tenant roles)
-- =============================================================
CREATE TABLE roles (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code                  TEXT NOT NULL UNIQUE,           -- 'teacher', 'principal', 'division_staff'
  name                  TEXT NOT NULL,
  description           TEXT,
  scope                 TEXT NOT NULL DEFAULT 'school'  -- 'system' | 'org' | 'school'
                      CHECK (scope IN ('system', 'org', 'school')),
  is_system             BOOLEAN NOT NULL DEFAULT FALSE, -- built-in role, cannot be deleted
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  display_order         INT NOT NULL DEFAULT 0,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- Seed core roles
INSERT INTO roles (code, name, description, scope, is_system, display_order) VALUES
  ('teacher',           'Teacher',           'Classroom teacher. Owns lesson plans, grades, and class roster.',                 'school', TRUE, 10),
  ('adviser',           'Class Adviser',     'Teacher with homeroom responsibilities. Additional access to advisership.',      'school', TRUE, 20),
  ('coordinator',       'Subject Coordinator','Coordinates a subject area across grade levels.',                              'school', TRUE, 30),
  ('head_teacher',      'Head Teacher',      'Department head. Approves lesson plans and grades within their department.',     'school', TRUE, 40),
  ('principal',         'School Principal',  'School head. Approves all school forms, reports, and major decisions.',          'school', TRUE, 50),
  ('school_head',       'School Head',       'Same as principal; alias used in some regions.',                                'school', TRUE, 60),
  ('ict_coordinator',   'ICT Coordinator',   'Manages school IT, DepEd LIS integration, and data submission.',                'school', TRUE, 70),
  ('guidance',          'Guidance Counselor','Access to intervention cases, parent comms, and student welfare records.',      'school', TRUE, 80),
  ('district_staff',    'District Staff',    'Read-only access to all schools in a district.',                                'org',    TRUE, 90),
  ('division_staff',    'Division Staff',    'Read-only + report access to all schools in a division.',                       'org',    TRUE, 100),
  ('region_staff',      'Region Staff',      'Read-only + analytics across all divisions in a region.',                       'org',    TRUE, 110),
  ('deped_admin',       'DepEd Administrator','Platform owner. Manages reference data, DepEd templates, and system config.',   'system', TRUE, 200),
  ('support_agent',     'Support Agent',     'Customer support. Bounded read-only access to diagnose issues.',                'system', TRUE, 210);

-- =============================================================
-- 7. permissions
-- =============================================================
CREATE TABLE permissions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code                  TEXT NOT NULL UNIQUE,           -- 'lesson_plan.create'
  name                  TEXT NOT NULL,
  description           TEXT,
  module                TEXT NOT NULL,                  -- 'academic', 'sis', 'forms', etc.
  action                TEXT NOT NULL,                  -- 'create' | 'read' | 'update' | 'delete' | 'approve' | 'export'
  resource              TEXT,                           -- 'lesson_plan', 'student', etc.
  is_sensitive          BOOLEAN NOT NULL DEFAULT FALSE, -- requires explicit grant
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_permissions_module ON permissions(module);
CREATE INDEX idx_permissions_action ON permissions(action);

-- =============================================================
-- 8. role_permissions
-- =============================================================
CREATE TABLE role_permissions (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  role_id               UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission_id         UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_perm ON role_permissions(permission_id);

-- =============================================================
-- 9. user_role_assignments  (user ↔ role ↔ tenant)
-- =============================================================
CREATE TABLE user_role_assignments (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id               UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
  tenant_id             UUID NOT NULL,                  -- school_id or org_id
  tenant_type           TEXT NOT NULL DEFAULT 'school' CHECK (tenant_type IN ('school','org')),
  school_year_id        UUID,                           -- optional: assignment for specific SY
  status                assignment_status NOT NULL DEFAULT 'active',
  start_date            DATE,
  end_date              DATE,
  is_primary            BOOLEAN NOT NULL DEFAULT FALSE, -- primary role in this tenant
  grade_levels          INT[],                          -- for teachers: which grade levels they handle
  subjects              TEXT[],                         -- for teachers: which subjects
  sections              UUID[],                         -- for advisers: which sections
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
  CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_user_role_assignments_user ON user_role_assignments(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_role_assignments_role ON user_role_assignments(role_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_role_assignments_tenant ON user_role_assignments(tenant_id) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_user_role_active_per_tenant
  ON user_role_assignments(user_id, role_id, tenant_id, school_year_id)
  WHERE deleted_at IS NULL;
-- One primary role per user per tenant
CREATE UNIQUE INDEX uq_user_primary_role_per_tenant
  ON user_role_assignments(user_id, tenant_id) WHERE is_primary = TRUE AND deleted_at IS NULL;

COMMENT ON TABLE user_role_assignments IS 'A user can hold multiple roles across multiple tenants. The "is_primary" flag indicates their main role in that tenant.';

-- =============================================================
-- 10. organization_members  (membership at the org/division level)
-- =============================================================
CREATE TABLE organization_members (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  organization_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  role_id               UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
  is_primary            BOOLEAN NOT NULL DEFAULT FALSE,
  status                assignment_status NOT NULL DEFAULT 'active',
  start_date            DATE,
  end_date              DATE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE UNIQUE INDEX uq_org_member_active
  ON organization_members(user_id, organization_id, role_id)
  WHERE deleted_at IS NULL;
CREATE INDEX idx_org_members_user ON organization_members(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_org_members_org ON organization_members(organization_id) WHERE deleted_at IS NULL;

COMMENT ON TABLE organization_members IS 'Org/division-level staff (district_staff, division_staff, region_staff).';

-- =============================================================
-- 11. school_memberships  (denormalized view: who belongs to which school)
-- =============================================================
CREATE TABLE school_memberships (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  school_id             UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
  role_id               UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
  school_year_id        UUID REFERENCES school_years(id) ON DELETE CASCADE,
  status                assignment_status NOT NULL DEFAULT 'active',
  is_adviser            BOOLEAN NOT NULL DEFAULT FALSE, -- shortcut for adviser-section lookups
  is_active_duty        BOOLEAN NOT NULL DEFAULT TRUE,  -- currently teaching (vs. on leave)
  start_date            DATE,
  end_date              DATE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_school_memberships_user ON school_memberships(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_school_memberships_school ON school_memberships(school_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_school_memberships_sy ON school_memberships(school_year_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_school_memberships_adviser ON school_memberships(school_id) WHERE is_adviser = TRUE AND deleted_at IS NULL;

COMMENT ON TABLE school_memberships IS 'Denormalized hot path for "who teaches at this school this SY". Materialized from user_role_assignments.';

-- =============================================================
-- 12. user_invitations  (pending invites)
-- =============================================================
CREATE TABLE user_invitations (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email                 CITEXT NOT NULL,
  school_id             UUID REFERENCES schools(id) ON DELETE CASCADE,
  organization_id       UUID REFERENCES organizations(id) ON DELETE CASCADE,
  role_id               UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
  school_year_id        UUID REFERENCES school_years(id) ON DELETE SET NULL,
  token_hash            TEXT NOT NULL UNIQUE,           -- bcrypt-hashed single-use token
  invited_by            UUID NOT NULL REFERENCES users(id),
  invited_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at            TIMESTAMPTZ NOT NULL,
  accepted_at           TIMESTAMPTZ,
  revoked_at            TIMESTAMPTZ,
  message               TEXT,
  status                TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired', 'revoked')),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
  CHECK (school_id IS NOT NULL OR organization_id IS NOT NULL)
);

CREATE INDEX idx_invitations_email ON user_invitations(email) WHERE status = 'pending';
CREATE INDEX idx_invitations_school ON user_invitations(school_id) WHERE status = 'pending';
CREATE INDEX idx_invitations_expires ON user_invitations(expires_at) WHERE status = 'pending';

COMMENT ON TABLE user_invitations IS 'Pending invitations. Token stored as bcrypt hash; plaintext token is sent via email/SMS and never persisted.';

-- =============================================================
-- 13. Triggers (apply to all auth tables)
-- =============================================================
DO $$
DECLARE
  t TEXT;
BEGIN
  FOR t IN
    SELECT unnest(ARRAY[
      'organizations', 'schools', 'school_years',
      'users', 'user_profiles', 'user_role_assignments',
      'organization_members', 'school_memberships',
      'user_invitations', 'role_permissions'
    ])
  LOOP
    EXECUTE format('
      CREATE TRIGGER tg_set_updated_at
        BEFORE UPDATE ON core.%I
        FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
    ', t);
  END LOOP;
END $$;

-- =============================================================
-- 14. RLS helper functions (used by every other module)
-- =============================================================
CREATE OR REPLACE FUNCTION core.current_tenant_id() RETURNS UUID
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.current_tenant_id', true), '')::UUID;
$$;

CREATE OR REPLACE FUNCTION core.current_user_id() RETURNS UUID
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.current_user_id', true), '')::UUID;
$$;

CREATE OR REPLACE FUNCTION core.current_role_code() RETURNS TEXT
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.current_role', true), '');
$$;

CREATE OR REPLACE FUNCTION core.is_tenant_admin() RETURNS BOOLEAN
LANGUAGE sql STABLE AS $$
  SELECT EXISTS (
    SELECT 1 FROM core.user_role_assignments ura
    JOIN core.roles r ON r.id = ura.role_id
    WHERE ura.user_id = core.current_user_id()
      AND ura.tenant_id = core.current_tenant_id()
      AND r.code IN ('principal','school_head','deped_admin','division_staff','region_staff','support_agent')
      AND ura.status = 'active'
      AND ura.deleted_at IS NULL
  );
$$;

CREATE OR REPLACE FUNCTION core.is_system_admin() RETURNS BOOLEAN
LANGUAGE sql STABLE AS $$
  SELECT COALESCE(NULLIF(current_setting('app.bypass_rls', true), ''), 'false')::BOOLEAN
      OR EXISTS (
        SELECT 1 FROM core.users
        WHERE id = core.current_user_id() AND is_super_admin = TRUE
      );
$$;

-- =============================================================
-- 15. RLS for organizations (read public, write admin)
-- =============================================================
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations FORCE ROW LEVEL SECURITY;

CREATE POLICY rls_organizations_select ON organizations
  FOR SELECT USING (deleted_at IS NULL OR core.is_system_admin());

CREATE POLICY rls_organizations_insert ON organizations
  FOR INSERT WITH CHECK (core.is_system_admin());

CREATE POLICY rls_organizations_update ON organizations
  FOR UPDATE USING (core.is_system_admin());

CREATE POLICY rls_organizations_delete ON organizations
  FOR DELETE USING (core.is_system_admin() AND type <> 'deped_central');

-- =============================================================
-- 16. RLS for schools
-- =============================================================
ALTER TABLE schools ENABLE ROW LEVEL SECURITY;
ALTER TABLE schools FORCE ROW LEVEL SECURITY;

CREATE POLICY rls_schools_select ON schools
  FOR SELECT USING (
    deleted_at IS NULL AND (
      core.is_system_admin()
      OR id = core.current_tenant_id()
      OR organization_id IN (
        SELECT organization_id FROM core.organization_members
        WHERE user_id = core.current_user_id() AND deleted_at IS NULL
      )
    )
  );

CREATE POLICY rls_schools_insert ON schools
  FOR INSERT WITH CHECK (core.is_system_admin());

CREATE POLICY rls_schools_update ON schools
  FOR UPDATE USING (
    id = core.current_tenant_id() AND (core.is_tenant_admin() OR core.is_system_admin())
  );

CREATE POLICY rls_schools_delete ON schools
  FOR DELETE USING (core.is_system_admin());

-- =============================================================
-- 17. RLS for school_years
-- =============================================================
ALTER TABLE school_years ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_years FORCE ROW LEVEL SECURITY;

CREATE POLICY rls_school_years_select ON school_years
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_school_years_write ON school_years
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin())
       WITH CHECK (core.is_tenant_admin() OR core.is_system_admin());

-- =============================================================
-- 18. RLS for users
-- =============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

-- Users can see themselves
CREATE POLICY rls_users_select_self ON users
  FOR SELECT USING (id = core.current_user_id() OR core.is_system_admin());

-- Users in same school can see each other (for class rosters, co-teachers)
CREATE POLICY rls_users_select_schoolmates ON users
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM core.school_memberships sm1
      JOIN core.school_memberships sm2 ON sm2.school_id = sm1.school_id
      WHERE sm1.user_id = core.current_user_id()
        AND sm2.user_id = users.id
        AND sm1.deleted_at IS NULL AND sm2.deleted_at IS NULL
    )
  );

CREATE POLICY rls_users_update_self ON users
  FOR UPDATE USING (id = core.current_user_id() OR core.is_system_admin());

CREATE POLICY rls_users_delete ON users
  FOR DELETE USING (core.is_system_admin());

-- =============================================================
-- 19. RLS for user_profiles
-- =============================================================
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles FORCE ROW LEVEL SECURITY;

CREATE POLICY rls_user_profiles_select ON user_profiles
  FOR SELECT USING (
    user_id = core.current_user_id()
    OR core.is_system_admin()
    OR EXISTS (
      SELECT 1 FROM core.school_memberships sm1
      JOIN core.school_memberships sm2 ON sm2.school_id = sm1.school_id
      WHERE sm1.user_id = core.current_user_id() AND sm2.user_id = user_profiles.user_id
        AND sm1.deleted_at IS NULL AND sm2.deleted_at IS NULL
    )
  );
CREATE POLICY rls_user_profiles_update ON user_profiles
  FOR UPDATE USING (user_id = core.current_user_id() OR core.is_system_admin());

-- =============================================================
-- 20. RLS for roles, permissions
-- =============================================================
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_roles_read ON roles FOR SELECT USING (TRUE);
CREATE POLICY rls_roles_write ON roles FOR ALL USING (core.is_system_admin());

ALTER TABLE permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE permissions FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_permissions_read ON permissions FOR SELECT USING (TRUE);
CREATE POLICY rls_permissions_write ON permissions FOR ALL USING (core.is_system_admin());

ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_role_permissions_read ON role_permissions FOR SELECT USING (TRUE);
CREATE POLICY rls_role_permissions_write ON role_permissions FOR ALL USING (core.is_system_admin());

-- =============================================================
-- 21. RLS for user_role_assignments
-- =============================================================
ALTER TABLE user_role_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_role_assignments FORCE ROW LEVEL SECURITY;

CREATE POLICY rls_ura_select ON user_role_assignments
  FOR SELECT USING (
    user_id = core.current_user_id()
    OR tenant_id = core.current_tenant_id()
    OR core.is_system_admin()
  );
CREATE POLICY rls_ura_write ON user_role_assignments
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

-- =============================================================
-- 22. RLS for organization_members, school_memberships
-- =============================================================
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_org_members_read ON organization_members
  FOR SELECT USING (user_id = core.current_user_id() OR core.is_tenant_admin() OR core.is_system_admin());
CREATE POLICY rls_org_members_write ON organization_members
  FOR ALL USING (core.is_system_admin());

ALTER TABLE school_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_memberships FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_school_memberships_read ON school_memberships
  FOR SELECT USING (
    user_id = core.current_user_id()
    OR school_id = core.current_tenant_id()
    OR core.is_system_admin()
  );
CREATE POLICY rls_school_memberships_write ON school_memberships
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

ALTER TABLE user_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_invitations FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_invitations_read ON user_invitations
  FOR SELECT USING (invited_by = core.current_user_id() OR core.is_tenant_admin() OR core.is_system_admin());
CREATE POLICY rls_invitations_write ON user_invitations
  FOR ALL USING (core.is_tenant_admin() OR core.is_system_admin());

-- =============================================================
-- 23. Auto-create user row when auth.users row is created (Supabase)
-- =============================================================
CREATE OR REPLACE FUNCTION core.tg_handle_new_user() RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO core.users (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger attached to auth.users in Supabase; commented out here for portability:
-- CREATE TRIGGER tg_on_auth_user_created
--   AFTER INSERT ON auth.users
--   FOR EACH ROW EXECUTE FUNCTION core.tg_handle_new_user();

COMMENT ON FUNCTION core.tg_handle_new_user() IS 'Creates a row in core.users whenever Supabase auth.users gets a new row.';

-- =============================================================
-- 24. Resolve deferred foreign keys
-- =============================================================
-- school_head_user_id requires users table to exist first
-- This ALTER TABLE runs AFTER all core tables are created
-- ALTER TABLE core.schools
--   ADD CONSTRAINT fk_schools_school_head
--   FOREIGN KEY (school_head_user_id) REFERENCES core.users(id)
--   ON DELETE SET NULL;

-- =============================================================
-- 25. deped_config  (parameterized configuration)
-- =============================================================
CREATE TABLE core.deped_config (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  config_key            TEXT NOT NULL UNIQUE,            -- 'melc_version', 'sf_template_version'
  config_value          TEXT NOT NULL,
  description           TEXT,
  effective_from        DATE NOT NULL DEFAULT CURRENT_DATE,
  effective_until       DATE,
  set_by                UUID,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_deped_config_key ON core.deped_config(config_key) WHERE deleted_at IS NULL;

COMMENT ON TABLE core.deped_config IS 'Centralized configuration for DepEd reference data versions. Replaces the hardcoded ''2020'' default in melcs.deped_version.';

-- Seed current values
INSERT INTO core.deped_config (config_key, config_value, description) VALUES
  ('melc_version', '2020', 'Current MELC matrix version (DepEd K-12)'),
  ('sf1_template_version', '2024-v1', 'Current SF1 template version'),
  ('sf2_template_version', '2024-v1', 'Current SF2 template version'),
  ('transmutation_table', 'deped_k12', 'Current transmutation table (DO 8, s. 2015)');

-- =============================================================
-- End of Module 1
-- =============================================================
