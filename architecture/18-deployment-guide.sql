-- =============================================================
-- 18. Deployment Guide & Operations
-- Run-in-order script, security grants, pg_cron schedules,
-- monitoring views, and disaster-recovery procedures
-- =============================================================

-- =============================================================
-- 18.1 Execution Order
-- =============================================================
-- 1. 01-auth-organization.sql
-- 2. 02-student-information.sql
-- 3. 03-lesson-planning.sql
-- 4. 04-assessments.sql
-- 5. 05-gradebook.sql
-- 6. 06-school-forms.sql
-- 7. 07-risk-intervention.sql
-- 8. 08-parent-communication.sql
-- 9. 09-reporting-compliance.sql
-- 10. 10-school-programs.sql
-- 11. 11-documents.sql
-- 12. 12-ai-agents.sql
-- 13. 13-workflow-engine.sql
-- 14. 14-audit-security.sql
-- 15. 15-rls-policies.sql (review-only; RLS already inline)
-- 16. 16-indexes.sql (review-only; indexes already inline)
-- 17. 17-materialized-views.sql
-- 18. 18-deployment-guide.sql (this file)

-- =============================================================
-- 18.2 Roles (Supabase-style)
-- =============================================================
-- In Supabase, the following roles are pre-created:
--   - authenticated  (every logged-in user)
--   - anon           (logged out)
--   - service_role   (bypasses RLS, used by Edge Functions)
-- We create app-level roles that map to those:

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_admin') THEN
    CREATE ROLE app_admin NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_service') THEN
    CREATE ROLE app_service NOLOGIN BYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_analytics') THEN
    CREATE ROLE app_analytics NOLOGIN;
  END IF;
END $$;

-- Grant usage on all schemas
GRANT USAGE ON SCHEMA
  core, sis, academic, assessment, gradebook, forms, intervention,
  comms, compliance, programs, documents, ai, workflow, audit, analytics
TO app_user, app_admin, app_service, app_analytics;

-- Grant SELECT/INSERT/UPDATE/DELETE on all tables to the service role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA
  core, sis, academic, assessment, gradebook, forms, intervention,
  comms, compliance, programs, documents, ai, workflow, audit, analytics
TO app_service;

-- Grant USAGE/SELECT on all sequences to service role
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA
  core, sis, academic, assessment, gradebook, forms, intervention,
  comms, compliance, programs, documents, ai, workflow, audit
TO app_service;

-- For app_user: only RLS-gated access (no direct grants beyond USAGE)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA
  core, sis, academic, assessment, gradebook, forms, intervention,
  comms, compliance, programs, documents, ai, workflow, audit
TO app_user;

-- For app_analytics: read-only on analytics schema + base tables
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO app_analytics;

-- =============================================================
-- 18.3 Connection Limits
-- =============================================================
-- ALTER ROLE app_user CONNECTION LIMIT 50;
-- ALTER ROLE app_admin CONNECTION LIMIT 30;
-- ALTER ROLE app_service CONNECTION LIMIT 10;
-- ALTER ROLE app_analytics CONNECTION LIMIT 5;

-- =============================================================
-- 18.4 Statement Timeouts
-- =============================================================
-- ALTER ROLE app_user SET statement_timeout = '30s';
-- ALTER ROLE app_admin SET statement_timeout = '60s';
-- ALTER ROLE app_service SET statement_timeout = '300s';
-- ALTER ROLE app_analytics SET statement_timeout = '120s';

-- =============================================================
-- 18.5 pg_cron Job Schedule (production)
-- =============================================================
-- The following jobs run automatically. Adjust cron expressions as needed.

-- Daily at 02:00 PH time (UTC+8): refresh most materialized views
-- SELECT cron.schedule('mv_teacher_productivity_nightly', '0 2 * * *',
--   $$REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_teacher_productivity$$);

-- Every 15 minutes: refresh at-risk (used by intervention dashboard)
-- SELECT cron.schedule('mv_at_risk_quarter_hour', '*/15 * * * *',
--   $$REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_at_risk_students$$);

-- Daily at 03:00: retention purge (delete old soft-deleted rows, archive audit logs)
-- SELECT cron.schedule('purge_soft_deleted', '0 3 * * *',
--   $$DELETE FROM audit_logs WHERE occurred_at < now() - interval '7 years'$$);

-- Hourly: process pending domain_events
-- SELECT cron.schedule('process_domain_events', '0 * * * *',
--   $$SELECT count(*) FROM audit.process_pending_events()$$);

-- Daily at 01:00: reindex heavily-updated tables (CONCURRENTLY)
-- SELECT cron.schedule('reindex_daily', '0 1 * * *',
--   $$REINDEX TABLE CONCURRENTLY audit.audit_logs$$);

-- Daily at 04:00: vacuum analyze large tables
-- SELECT cron.schedule('vacuum_analyze_daily', '0 4 * * *',
--   $$VACUUM ANALYZE audit.audit_logs, sis.attendance_records$$);

-- Weekly: archive documents older than 1 year to cold storage
-- (Implementation depends on the object storage provider)

-- =============================================================
-- 18.6 Required PostgreSQL Extensions
-- =============================================================
-- These are installed at the top of 01-auth-organization.sql, but listed here for ops:
CREATE EXTENSION IF NOT EXISTS pgcrypto;       -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS citext;         -- case-insensitive email
CREATE EXTENSION IF NOT EXISTS btree_gist;     -- exclusion constraints
CREATE EXTENSION IF NOT EXISTS pg_trgm;         -- text search (GIN)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";    -- legacy UUID v1
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;  -- query monitoring
CREATE EXTENSION IF NOT EXISTS pgaudit;         -- audit logging (optional, Supabase)

-- Recommended but not required:
-- CREATE EXTENSION IF NOT EXISTS pg_cron;        -- scheduled jobs
-- CREATE EXTENSION IF NOT EXISTS timescaledb;   -- for time-series scaling
-- CREATE EXTENSION IF NOT EXISTS postgis;        -- geo features

-- =============================================================
-- 18.7 Security Grants to Enforce in Production
-- =============================================================
-- Once RLS is in place, REVOKE broad table grants from app_user.
-- The app uses a per-request role-switching pattern, so app_user
-- should not have any direct table grants.

-- Example (do this AFTER RLS is verified):
-- REVOKE ALL ON ALL TABLES IN SCHEMA core FROM app_user;
-- REVOKE ALL ON ALL TABLES IN SCHEMA sis FROM app_user;
-- ... etc.

-- The app's connection pooler (Supavisor / PgBouncer) sets the
-- session variables before each query:
--   SET LOCAL app.current_user_id = '...';
--   SET LOCAL app.current_tenant_id = '...';
--   SET LOCAL app.current_role = 'teacher';
--   SET LOCAL app.bypass_rls = 'false';

-- =============================================================
-- 18.8 Health Check Queries
-- =============================================================
-- These are the queries that the deployment health-check endpoint runs.
-- Each should return in < 1 second.

-- Check 1: All required schemas exist
-- SELECT nspname FROM pg_namespace
-- WHERE nspname IN ('core','sis','academic','assessment','gradebook','forms','intervention','comms','compliance','programs','documents','ai','workflow','audit','analytics');

-- Check 2: All required tables have RLS
-- SELECT schemaname, tablename FROM pg_tables
-- WHERE schemaname NOT IN ('pg_catalog','information_schema') AND NOT rowsecurity;

-- Check 3: All required enums exist
-- SELECT typname FROM pg_type
-- WHERE typtype = 'e' AND typname LIKE '%_AS_%' OR typtype = 'e';

-- Check 4: Refresh age of materialized views
-- SELECT schemaname, matviewname, last_refresh
-- FROM pg_stat_user_tables
-- WHERE schemaname = 'analytics';

-- Check 5: Database size
-- SELECT pg_size_pretty(pg_database_size(current_database()));

-- Check 6: Active connections
-- SELECT count(*), state FROM pg_stat_activity GROUP BY state;

-- =============================================================
-- 18.9 Data Migration Strategy
-- =============================================================
-- When migrating from existing SIS systems (e.g., LIS, LIS-DepEd):

-- Phase 1: Ingest MELCs and SF templates (one-time)
-- INSERT INTO academic.melcs (...) SELECT * FROM staging.deped_melcs_csv
-- ON CONFLICT (code) DO NOTHING;

-- Phase 2: Ingest schools and organizations
-- INSERT INTO core.organizations (...) SELECT * FROM staging.schools_csv;

-- Phase 3: Ingest users (with Supabase auth.users pre-created)
-- INSERT INTO core.users (id, email) SELECT id, email FROM staging.users_csv;

-- Phase 4: Ingest students
-- Use COPY for bulk inserts, then UPDATE to set current_school_id

-- Phase 5: Verify data integrity
-- SELECT count(*) FROM sis.students WHERE LRN IS NULL;
-- SELECT count(*) FROM sis.student_enrollments WHERE section_id IS NULL;

-- Phase 6: Cut over (read-only first, then full)
-- Update DNS / API endpoint to point to new system
-- Run dual-write for 1 week
-- Decommission old system

-- =============================================================
-- 18.10 Disaster Recovery Runbook
-- =============================================================
-- RTO: 30 min
-- RPO: 5 min

-- SCENARIO: Primary database is unavailable
-- 1. Detect via health check
-- 2. Promote standby: SELECT pg_promote(); (if using streaming replication)
-- 3. Update DNS / connection string to point to standby
-- 4. Verify the read replica is not being used (it would lose writes)
-- 5. Reroute traffic
-- 6. Communicate to users
-- 7. Once primary is back: reverse the flow, re-replicate

-- SCENARIO: Data corruption (bad deploy, malicious actor)
-- 1. Identify the bad data and the timestamp of corruption
-- 2. Take a snapshot of the current state for forensics
-- 3. Use PITR: pg_restore --target-time '2026-06-08 10:00:00'
-- 4. Verify the restored DB
-- 5. Communicate before cutting over

-- SCENARIO: Accidental data deletion by user
-- 1. Identify the user, time, and tables
-- 2. Since soft delete is used, just UPDATE deleted_at = NULL for those rows
-- 3. Or use audit_logs to find before/after state, write recovery script

-- =============================================================
-- 18.11 Compliance Checklists
-- =============================================================
-- DepEd Data Privacy Act of 2012 (RA 10173):
-- [✓] PII encrypted at rest (handled by cloud provider)
-- [✓] PII encrypted in transit (TLS)
-- [✓] Access control via RLS
-- [✓] Audit logging of all data access
-- [✓] Right to data portability (export endpoints)
-- [✓] Data minimization (only collect what's needed)
-- [✓] Retention policy (7 years for audit, configurable for others)

-- DepEd Reporting Requirements:
-- [✓] SF1 (School Register) - forms.school_forms WHERE form_code = 'SF1'
-- [✓] SF2 (Daily Attendance) - forms.school_forms WHERE form_code = 'SF2'
-- [✓] SF5 (Promotion) - forms.school_forms WHERE form_code = 'SF5'
-- [✓] SF9 (Progress Report) - forms.school_forms WHERE form_code = 'SF9'
-- [✓] SF10 (Permanent Record) - forms.school_forms WHERE form_code = 'SF10'
-- [✓] RPMS - compliance.reports WHERE kind = 'rpms'
-- [✓] MELC alignment - academic.melcs + academic.lesson_plans
-- [✓] Quarterly grading - gradebook.computed_grades
-- [✓] DepEd transmutation - gradebook.deped_transmute()
-- [✓] BRIGADA Eskwela - programs.programs WHERE category = 'brigada_eskwela'
-- [✓] DRRM - programs.programs WHERE category = 'drrrm'
-- [✓] School-Based Feeding Program - programs.programs WHERE category = 'feeding'

-- =============================================================
-- 18.12 Open Items (not in scope of v1.0)
-- =============================================================
-- - SMS/MMS support via MMS gateway (for richer media)
-- - Video conferencing integration for parent-teacher meetings
-- - Mobile push notifications (FCM/APNS) - currently in_app + email + SMS only
-- - Offline-first PWA sync protocol (currently requires connectivity)
-- - AI agent marketplace (3rd party agents)
-- - SSO integration with DepEd LIS (deped.gov.ph)
-- - Blockchain anchoring for school form submissions (optional)
-- - Multi-language UI (currently English + Filipino via i18n)
-- - Parent self-service portal (read-only views for parents)
-- - Student self-service portal (view own grades, assignments)

-- =============================================================
-- End of 18
-- =============================================================
