"""PostgreSQL Row-Level Security (RLS) policies for tenant isolation.

These SQL statements implement strict tenant isolation at the database level.
Every table that stores multi-tenant data must include:
- organization_id (UUID, NOT NULL)
- school_id (UUID, NOT NULL)

RLS policies ensure that:
- A Teacher from School A CANNOT access School B data
- Cross-school data access is prevented at the database level
- Even direct SQL queries respect tenant boundaries

Apply these policies during database migrations.
"""

# ---------------------------------------------------------------------------
# Enable RLS on all multi-tenant tables
# ---------------------------------------------------------------------------

ENABLE_RLS_SQL = """
-- Enable Row-Level Security on multi-tenant tables
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE grades ENABLE ROW LEVEL SECURITY;
ALTER TABLE forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE interventions ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_interactions ENABLE ROW LEVEL SECURITY;
"""

# ---------------------------------------------------------------------------
# Tenant Isolation Policy (most restrictive)
# ---------------------------------------------------------------------------

TENANT_ISOLATION_POLICY_SQL = """
-- FOR ALL OPERATIONS: Users can only access data within their tenant
-- This is the primary isolation policy that prevents cross-school access.

CREATE POLICY tenant_isolation_select ON students
    FOR SELECT
    USING (organization_id = current_setting('app.current_organization_id')::uuid
           AND school_id = current_setting('app.current_school_id')::uuid);

CREATE POLICY tenant_isolation_insert ON students
    FOR INSERT
    WITH CHECK (organization_id = current_setting('app.current_organization_id')::uuid
                AND school_id = current_setting('app.current_school_id')::uuid);

CREATE POLICY tenant_isolation_update ON students
    FOR UPDATE
    USING (organization_id = current_setting('app.current_organization_id')::uuid
           AND school_id = current_setting('app.current_school_id')::uuid)
    WITH CHECK (organization_id = current_setting('app.current_organization_id')::uuid
                AND school_id = current_setting('app.current_school_id')::uuid);

CREATE POLICY tenant_isolation_delete ON students
    FOR DELETE
    USING (organization_id = current_setting('app.current_organization_id')::uuid
           AND school_id = current_setting('app.current_school_id')::uuid);
"""

# ---------------------------------------------------------------------------
# Example: RLS for attendance table
# ---------------------------------------------------------------------------

ATTENDANCE_RLS_SQL = """
CREATE POLICY attendance_tenant_isolation_select ON attendance
    FOR SELECT
    USING (organization_id = current_setting('app.current_organization_id')::uuid
           AND school_id = current_setting('app.current_school_id')::uuid);

CREATE POLICY attendance_tenant_isolation_insert ON attendance
    FOR INSERT
    WITH CHECK (organization_id = current_setting('app.current_organization_id')::uuid
                AND school_id = current_setting('app.current_school_id')::uuid);

CREATE POLICY attendance_tenant_isolation_update ON attendance
    FOR UPDATE
    USING (organization_id = current_setting('app.current_organization_id')::uuid
           AND school_id = current_setting('app.current_school_id')::uuid)
    WITH CHECK (organization_id = current_setting('app.current_organization_id')::uuid
                AND school_id = current_setting('app.current_school_id')::uuid);

CREATE POLICY attendance_tenant_isolation_delete ON attendance
    FOR DELETE
    USING (organization_id = current_setting('app.current_organization_id')::uuid
           AND school_id = current_setting('app.current_school_id')::uuid);
"""

# ---------------------------------------------------------------------------
# Example: RLS for grades table (with adviser access for their sections)
# ---------------------------------------------------------------------------

GRADES_RLS_SQL = """
-- Base tenant isolation for grades
CREATE POLICY grades_tenant_isolation ON grades
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id')::uuid
           AND school_id = current_setting('app.current_school_id')::uuid);

-- Advisers can read grades for their advisory section
CREATE POLICY grades_adviser_read ON grades
    FOR SELECT
    USING (
        organization_id = current_setting('app.current_organization_id')::uuid
        AND school_id = current_setting('app.current_school_id')::uuid
        AND (section_id IN (
            SELECT advisory_section_id FROM users
            WHERE id = current_setting('app.current_user_id')::uuid
            AND role = 'adviser'
        ) OR current_setting('app.current_user_role') IN ('principal', 'school_head', 'division_staff', 'super_admin'))
    );
"""

# ---------------------------------------------------------------------------
# Example: RLS for forms (school forms are school-scoped)
# ---------------------------------------------------------------------------

FORMS_RLS_SQL = """
CREATE POLICY forms_tenant_isolation ON forms
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id')::uuid
           AND school_id = current_setting('app.current_school_id')::uuid);
"""

# ---------------------------------------------------------------------------
# Example: RLS for documents (uploaded files)
# ---------------------------------------------------------------------------

DOCUMENTS_RLS_SQL = """
CREATE POLICY documents_tenant_isolation ON documents
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id')::uuid
           AND school_id = current_setting('app.current_school_id')::uuid);
"""

# ---------------------------------------------------------------------------
# Audit Log RLS (append-only prevention)
# ---------------------------------------------------------------------------

AUDIT_LOG_RLS_SQL = """
-- Audit logs are append-only: only INSERT and SELECT are allowed
CREATE POLICY audit_logs_insert ON audit_logs
    FOR INSERT
    WITH CHECK (true);  -- Anyone can append to audit logs

CREATE POLICY audit_logs_select ON audit_logs
    FOR SELECT
    USING (organization_id = current_setting('app.current_organization_id')::uuid
           AND school_id = current_setting('app.current_school_id')::uuid);

-- Revoke UPDATE and DELETE on audit_logs from all roles
REVOKE UPDATE, DELETE ON audit_logs FROM PUBLIC;
REVOKE UPDATE, DELETE ON audit_logs FROM teacher, adviser, coordinator, principal, school_head, division_staff;
-- Only super_admin can manage audit logs
GRANT UPDATE, DELETE ON audit_logs TO super_admin;
"""

# ---------------------------------------------------------------------------
# Helper: Setting app context in PostgreSQL
# ---------------------------------------------------------------------------

SET_TENANT_CONTEXT_SQL = """
-- This is called at the start of each request
-- Sets the current tenant context for RLS enforcement

SELECT set_config('app.current_organization_id', :organization_id, true);
SELECT set_config('app.current_school_id', :school_id, true);
SELECT set_config('app.current_user_id', :user_id, true);
SELECT set_config('app.current_user_role', :role, true);
SELECT set_config('app.current_tenant_id', :tenant_id, true);
"""

# ---------------------------------------------------------------------------
# Comprehensive RLS Migration Script
# ---------------------------------------------------------------------------

FULL_RLS_MIGRATION_SQL = f"""
-- ==========================================================================
-- TeacherOS RLS Migration
-- Enables Row-Level Security for all multi-tenant tables
-- ==========================================================================

-- 1. Enable RLS on all tables
{ENABLE_RLS_SQL}

-- 2. Drop existing policies (for idempotency)
DROP POLICY IF EXISTS tenant_isolation_select ON students;
DROP POLICY IF EXISTS tenant_isolation_insert ON students;
DROP POLICY IF EXISTS tenant_isolation_update ON students;
DROP POLICY IF EXISTS tenant_isolation_delete ON students;
DROP POLICY IF EXISTS attendance_tenant_isolation_select ON attendance;
DROP POLICY IF EXISTS attendance_tenant_isolation_insert ON attendance;
DROP POLICY IF EXISTS attendance_tenant_isolation_update ON attendance;
DROP POLICY IF EXISTS attendance_tenant_isolation_delete ON attendance;
DROP POLICY IF EXISTS grades_tenant_isolation ON grades;
DROP POLICY IF EXISTS grades_adviser_read ON grades;
DROP POLICY IF EXISTS forms_tenant_isolation ON forms;
DROP POLICY IF EXISTS documents_tenant_isolation ON documents;
DROP POLICY IF EXISTS audit_logs_insert ON audit_logs;
DROP POLICY IF EXISTS audit_logs_select ON audit_logs;

-- 3. Create isolation policies
{TENANT_ISOLATION_POLICY_SQL}
{ATTENDANCE_RLS_SQL}
{GRADES_RLS_SQL}
{FORMS_RLS_SQL}
{DOCUMENTS_RLS_SQL}
{AUDIT_LOG_RLS_SQL}

-- 4. Ensure tables have required tenant columns
-- These should be added if not already present:
-- ALTER TABLE students ADD COLUMN IF NOT EXISTS organization_id UUID NOT NULL;
-- ALTER TABLE students ADD COLUMN IF NOT EXISTS school_id UUID NOT NULL;
-- ... (repeat for all multi-tenant tables)
"""


class RLSPolicyBuilder:
    """Builds and manages PostgreSQL RLS policies.

    Provides methods to generate RLS SQL for tenant isolation,
    and to create the tenant context setting function.
    """

    @staticmethod
    def get_create_context_function_sql() -> str:
        """Generate SQL for a PostgreSQL function that sets tenant context.

        This function is called at the beginning of each request.
        """
        return """
        CREATE OR REPLACE FUNCTION set_tenant_context(
            p_organization_id UUID,
            p_school_id UUID,
            p_user_id UUID,
            p_role TEXT,
            p_tenant_id TEXT DEFAULT NULL
        ) RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.current_organization_id', p_organization_id::text, true);
            PERFORM set_config('app.current_school_id', p_school_id::text, true);
            PERFORM set_config('app.current_user_id', p_user_id::text, true);
            PERFORM set_config('app.current_user_role', p_role, true);
            IF p_tenant_id IS NOT NULL THEN
                PERFORM set_config('app.current_tenant_id', p_tenant_id, true);
            END IF;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        """

    @staticmethod
    def get_tenant_column_alter_sql(table_name: str) -> str:
        """Generate SQL to add tenant columns to a table if missing."""
        return f"""
        ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS organization_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000';
        ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS school_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000';
        CREATE INDEX IF NOT EXISTS idx_{table_name}_org_school ON {table_name}(organization_id, school_id);
        """

    @staticmethod
    def get_full_migration_sql() -> str:
        """Get the complete RLS migration SQL."""
        return FULL_RLS_MIGRATION_SQL