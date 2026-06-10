-- =============================================================
-- Module 14: Audit & Security
-- Depends on: 01-auth-organization.sql
-- Tables: audit_logs, activity_logs, login_history,
--         notifications, notification_preferences
-- =============================================================

CREATE SCHEMA IF NOT EXISTS audit;
SET search_path TO audit, core, public;

CREATE TYPE audit_event_kind AS ENUM (
  'auth.login', 'auth.logout', 'auth.failed_login', 'auth.mfa_enabled', 'auth.password_changed',
  'rbac.role_granted', 'rbac.role_revoked', 'rbac.permission_denied',
  'data.created', 'data.updated', 'data.deleted', 'data.viewed', 'data.exported',
  'workflow.step_approved', 'workflow.step_rejected', 'workflow.workflow_started', 'workflow.workflow_completed',
  'ai.run_started', 'ai.run_completed', 'ai.output_approved', 'ai.output_rejected',
  'system.config_changed', 'system.scheduled_job_run', 'system.scheduled_job_failed',
  'security.suspicious_activity', 'security.data_export_large', 'security.pii_accessed'
);

CREATE TYPE audit_severity AS ENUM ('info','notice','warning','critical');
CREATE TYPE notification_channel AS ENUM ('in_app','email','sms','push','webhook');
CREATE TYPE notification_status AS ENUM ('pending','sent','delivered','read','failed');

-- =============================================================
-- 1. audit_logs  (append-only, immutable)
-- =============================================================
CREATE TABLE audit_logs (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,
  event_kind            audit_event_kind NOT NULL,
  severity              audit_severity NOT NULL DEFAULT 'info',
  actor_user_id         UUID,
  actor_role            TEXT,
  actor_ip              INET,
  actor_user_agent      TEXT,
  target_type           TEXT,
  target_id             UUID,
  target_label          TEXT,
  before_state          JSONB,
  after_state           JSONB,
  request_id            TEXT,
  session_id            TEXT,
  contains_pii          BOOLEAN NOT NULL DEFAULT FALSE,
  occurred_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id, occurred_at DESC);
CREATE INDEX idx_audit_actor ON audit_logs(actor_user_id, occurred_at DESC) WHERE actor_user_id IS NOT NULL;
CREATE INDEX idx_audit_target ON audit_logs(target_type, target_id) WHERE target_id IS NOT NULL;
CREATE INDEX idx_audit_kind ON audit_logs(event_kind, occurred_at DESC);
CREATE INDEX idx_audit_severity ON audit_logs(severity, occurred_at DESC) WHERE severity IN ('warning','critical');
CREATE INDEX idx_audit_pii ON audit_logs(occurred_at DESC) WHERE contains_pii = TRUE;
CREATE INDEX idx_audit_occurred_brin ON audit_logs USING brin (occurred_at);

COMMENT ON TABLE audit_logs IS 'Append-only. NEVER updated or deleted. Revoke UPDATE/DELETE in production.';

-- Enforce immutability
CREATE OR REPLACE FUNCTION audit.tg_block_modification() RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'audit_logs is append-only. UPDATE/DELETE is not permitted.';
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_block_update BEFORE UPDATE ON audit_logs
  FOR EACH ROW EXECUTE FUNCTION audit.tg_block_modification();
CREATE TRIGGER tg_block_delete BEFORE DELETE ON audit_logs
  FOR EACH ROW EXECUTE FUNCTION audit.tg_block_modification();

-- =============================================================
-- 2. activity_logs  (user-facing activity feed)
-- =============================================================
CREATE TABLE activity_logs (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  actor_user_id         UUID NOT NULL,
  activity_type         TEXT NOT NULL,
  verb                  TEXT NOT NULL,
  object_type           TEXT NOT NULL,
  object_id             UUID NOT NULL,
  object_label          TEXT,
  context_url           TEXT,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_public             BOOLEAN NOT NULL DEFAULT FALSE,
  occurred_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_activity_tenant ON activity_logs(tenant_id, occurred_at DESC);
CREATE INDEX idx_activity_actor ON activity_logs(actor_user_id, occurred_at DESC);
CREATE INDEX idx_activity_object ON activity_logs(object_type, object_id);
CREATE INDEX idx_activity_public ON activity_logs(tenant_id, occurred_at DESC) WHERE is_public = TRUE;

-- =============================================================
-- 3. login_history
-- =============================================================
CREATE TABLE login_history (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,
  user_id               UUID,
  email                 CITEXT,
  event_kind            TEXT NOT NULL,
  success               BOOLEAN NOT NULL,
  failure_reason        TEXT,
  ip_address            INET,
  user_agent            TEXT,
  device_fingerprint    TEXT,
  geo_country           TEXT,
  geo_city              TEXT,
  suspicious            BOOLEAN NOT NULL DEFAULT FALSE,
  suspicious_reason     TEXT,
  occurred_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_login_user ON login_history(user_id, occurred_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX idx_login_email ON login_history(email, occurred_at DESC) WHERE email IS NOT NULL;
CREATE INDEX idx_login_ip ON login_history(ip_address, occurred_at DESC);
CREATE INDEX idx_login_failed ON login_history(occurred_at DESC) WHERE success = FALSE;
CREATE INDEX idx_login_suspicious ON login_history(occurred_at DESC) WHERE suspicious = TRUE;

-- =============================================================
-- 4. notifications
-- =============================================================
CREATE TABLE notifications (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  recipient_user_id     UUID NOT NULL,
  notification_kind     TEXT NOT NULL,
  title                 TEXT NOT NULL,
  body                  TEXT,
  action_url            TEXT,
  action_label          TEXT,
  source_type           TEXT,
  source_id             UUID,
  priority              TEXT NOT NULL DEFAULT 'normal' CHECK (priority IN ('low','normal','high','urgent')),
  channels              notification_channel[] NOT NULL DEFAULT '{in_app}',
  status                notification_status NOT NULL DEFAULT 'pending',
  delivered_at          TIMESTAMPTZ,
  read_at               TIMESTAMPTZ,
  clicked_at            TIMESTAMPTZ,
  group_key             TEXT,
  expires_at            TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_notif_tenant ON notifications(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_notif_recipient ON notifications(recipient_user_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_notif_unread ON notifications(recipient_user_id) WHERE read_at IS NULL AND deleted_at IS NULL;
CREATE INDEX idx_notif_kind ON notifications(recipient_user_id, notification_kind) WHERE deleted_at IS NULL;
CREATE INDEX idx_notif_pending_send ON notifications(status) WHERE status = 'pending' AND deleted_at IS NULL;
CREATE INDEX idx_notif_group ON notifications(group_key) WHERE group_key IS NOT NULL;

-- =============================================================
-- 5. notification_preferences
-- =============================================================
CREATE TABLE notification_preferences (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  user_id               UUID NOT NULL,
  notification_kind     TEXT NOT NULL,
  channel               notification_channel NOT NULL,
  enabled               BOOLEAN NOT NULL DEFAULT TRUE,
  quiet_hours_start     TIME,
  quiet_hours_end       TIME,
  max_per_day           INT,
  digest_mode           TEXT DEFAULT 'immediate' CHECK (digest_mode IN ('immediate','hourly','daily','weekly','off')),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, notification_kind, channel)
);

CREATE INDEX idx_np_user ON notification_preferences(user_id);

-- =============================================================
-- 6. RLS
-- =============================================================
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_audit_read ON audit_logs
  FOR SELECT USING (
    core.is_tenant_admin() OR core.is_system_admin()
    OR actor_user_id = core.current_user_id()
  );
-- Restricted: only system triggers (bypass_rls = true) can insert audit entries
CREATE POLICY rls_audit_insert ON audit_logs FOR INSERT WITH CHECK (
  COALESCE(NULLIF(current_setting('app.bypass_rls', true), ''), 'false')::BOOLEAN = TRUE
);

ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_activity_read ON activity_logs
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_activity_write ON activity_logs
  FOR INSERT WITH CHECK (tenant_id = core.current_tenant_id() AND core.current_user_id() IS NOT NULL);

ALTER TABLE login_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_history FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_login_read ON login_history
  FOR SELECT USING (
    (user_id = core.current_user_id()) OR core.is_tenant_admin() OR core.is_system_admin()
  );
CREATE POLICY rls_login_write ON login_history FOR INSERT WITH CHECK (TRUE);

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_notif_read ON notifications
  FOR SELECT USING (recipient_user_id = core.current_user_id() OR core.is_system_admin());
CREATE POLICY rls_notif_update ON notifications
  FOR UPDATE USING (recipient_user_id = core.current_user_id());
CREATE POLICY rls_notif_insert ON notifications
  FOR INSERT WITH CHECK (tenant_id = core.current_tenant_id());

ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_preferences FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_np_read ON notification_preferences
  FOR SELECT USING (user_id = core.current_user_id() OR core.is_system_admin());
-- Protects against a compromised session setting a different user_id
CREATE POLICY rls_np_insert ON notification_preferences
  FOR INSERT WITH CHECK (user_id = core.current_user_id() OR core.is_system_admin());
CREATE POLICY rls_np_update ON notification_preferences
  FOR UPDATE USING (user_id = core.current_user_id() OR core.is_system_admin());
CREATE POLICY rls_np_delete ON notification_preferences
  FOR DELETE USING (core.is_system_admin());

-- =============================================================
-- 7. Triggers
-- =============================================================
DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY['activity_logs','login_history','notifications','notification_preferences'])
  LOOP
    EXECUTE format('CREATE TRIGGER tg_set_updated_at BEFORE UPDATE ON audit.%I FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();', t);
  END LOOP;
END $$;

-- =============================================================
-- End of Module 14
-- =============================================================
