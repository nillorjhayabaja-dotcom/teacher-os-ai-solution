-- =============================================================================
-- TeacherOS - PostgreSQL Initialization Script
-- =============================================================================
-- This script runs on first container startup to:
-- 1. Create extensions (pgvector, uuid-ossp, pgcrypto)
-- 2. Create custom types
-- 3. Create initial schema if needed
-- 4. Seed initial data
-- =============================================================================

-- =============================================================================
-- Extensions
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- =============================================================================
-- Schema
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS teacher_os;
CREATE SCHEMA IF NOT EXISTS audit;

-- =============================================================================
-- Custom Types
-- =============================================================================
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('super_admin', 'school_admin', 'teacher', 'parent', 'student');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE attendance_status AS ENUM ('present', 'absent', 'late', 'excused', 'holiday');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE grade_type AS ENUM ('quiz', 'exam', 'assignment', 'project', 'participation', 'final');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE school_type AS ENUM ('public', 'private', 'charter', 'international');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ai_task_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE report_type AS ENUM ('progress', 'report_card', 'attendance', 'behavior', 'custom');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- Search Configuration (for full-text search)
-- =============================================================================
DO $$ BEGIN
    CREATE TEXT SEARCH DICTIONARY english_stem (
        TEMPLATE = snowball,
        Language = english
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- Performance Configuration
-- =============================================================================
-- Set appropriate parameters for containerized PostgreSQL
ALTER SYSTEM SET max_connections = '200';
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '768MB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET random_page_cost = '1.1';
ALTER SYSTEM SET effective_io_concurrency = '200';
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = '100';
ALTER SYSTEM SET logging_collector = 'on';
ALTER SYSTEM SET log_min_duration_statement = '1000';
ALTER SYSTEM SET log_line_prefix = '%t [%p-%l] %q%u@%d ';

-- =============================================================================
-- Initial Data Seed
-- =============================================================================
-- Create default admin role if users table exists (will be created by Alembic)
-- This provides fallback if Alembic hasn't run yet

-- Insert default tenant
INSERT INTO teacher_os.tenants (id, name, slug, domain, school_type, address, contact_email, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Default School',
    'default',
    'localhost',
    'private',
    'Default Address',
    'admin@teacheros.ph',
    true
) ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- Grant Permissions
-- =============================================================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO teacheros;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO teacheros;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO teacheros;

GRANT USAGE ON SCHEMA teacher_os TO teacheros;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA teacher_os TO teacheros;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA teacher_os TO teacheros;

GRANT USAGE ON SCHEMA audit TO teacheros;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO teacheros;