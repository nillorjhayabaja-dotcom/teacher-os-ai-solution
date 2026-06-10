-- =============================================================
-- Module 8: Parent Communication
-- Depends on: 01-auth-organization.sql, 02-student-information.sql
-- Tables: communications, communication_templates,
--         communication_logs, communication_recipients,
--         home_visits, parent_conferences, sms_outbox
-- =============================================================

CREATE SCHEMA IF NOT EXISTS comms;
SET search_path TO comms, sis, core, public;

-- =============================================================
-- ENUMS
-- =============================================================
CREATE TYPE communication_channel AS ENUM (
  'sms', 'email', 'in_app', 'phone_call', 'home_visit', 'parent_conference',
  'letter', 'video_call', 'messaging_app'
);

CREATE TYPE communication_direction AS ENUM (
  'outbound', 'inbound'
);

CREATE TYPE communication_status AS ENUM (
  'draft', 'scheduled', 'sending', 'sent', 'delivered', 'read',
  'failed', 'bounced', 'replied', 'archived'
);

CREATE TYPE communication_purpose AS ENUM (
  'announcement', 'reminder', 'grade_release', 'attendance_alert',
  'parent_conference_request', 'incident_report', 'good_news',
  'absent_notification', 'event_invitation', 'permission_request',
  'report_card', 'intervention_update', 'general', 'other'
);

CREATE TYPE sms_provider AS ENUM (
  'twilio', 'semaphore', 'vonage', 'globe_labs', 'smart_devnet', 'custom'
);

CREATE TYPE sms_status AS ENUM (
  'queued', 'sent', 'delivered', 'failed', 'undelivered', 'received'
);

-- =============================================================
-- 1. communication_templates
-- =============================================================
CREATE TABLE communication_templates (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID,                           -- NULL for DepEd-issued
  name                  TEXT NOT NULL,
  code                  TEXT,                           -- 'grade-release-q1'
  purpose               communication_purpose NOT NULL,
  channel               communication_channel NOT NULL,
  language              TEXT NOT NULL DEFAULT 'en',
  subject               TEXT,                           -- for email
  body_template         TEXT NOT NULL,                  -- uses {{mustache}} placeholders
  body_html             TEXT,
  sms_segment_count     INT,                            -- pre-computed for SMS billing
  is_ai_generated       BOOLEAN NOT NULL DEFAULT FALSE,
  is_official           BOOLEAN NOT NULL DEFAULT FALSE, -- DepEd-issued
  variables_schema      JSONB NOT NULL DEFAULT '[]',    -- declares the placeholders
  usage_count           INT NOT NULL DEFAULT 0,
  is_active             BOOLEAN NOT NULL DEFAULT TRUE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  UNIQUE (tenant_id, code, language)
);

CREATE INDEX idx_ct_tenant ON communication_templates(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_ct_purpose ON communication_templates(purpose) WHERE deleted_at IS NULL;
CREATE INDEX idx_ct_official ON communication_templates(is_official) WHERE is_official = TRUE AND deleted_at IS NULL;

-- =============================================================
-- 2. communications  (one row per comm message)
-- =============================================================
CREATE TABLE communications (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,                  -- school_id
  school_year_id        UUID,
  template_id           UUID REFERENCES communication_templates(id) ON DELETE SET NULL,
  channel               communication_channel NOT NULL,
  direction             communication_direction NOT NULL DEFAULT 'outbound',
  purpose               communication_purpose NOT NULL,
  subject               TEXT,
  body                  TEXT NOT NULL,
  body_html             TEXT,
  -- The initiator
  initiated_by          UUID,                           -- NULL for system-sent
  initiated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  -- The student context (if applicable)
  student_id            UUID,
  section_id            UUID,
  -- Scheduling
  scheduled_at          TIMESTAMPTZ,                    -- when to send
  -- Status
  status                communication_status NOT NULL DEFAULT 'draft',
  -- Counts (denormalized for fast queries)
  recipient_count       INT NOT NULL DEFAULT 0,
  delivered_count       INT NOT NULL DEFAULT 0,
  read_count            INT NOT NULL DEFAULT 0,
  reply_count           INT NOT NULL DEFAULT 0,
  failed_count          INT NOT NULL DEFAULT 0,
  -- AI
  is_ai_generated       BOOLEAN NOT NULL DEFAULT FALSE,
  ai_output_id          UUID,                           -- ai.ai_outputs.id
  -- Cost
  estimated_cost        NUMERIC(10,4),
  actual_cost           NUMERIC(10,4),
  -- Attachments
  attachments           UUID[],                         -- documents.documents.id
  -- Variables used
  variables             JSONB,                          -- {"student_name": "...", "grade": "85"}
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ,
  metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_comms_tenant ON communications(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_comms_student ON communications(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_comms_status ON communications(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_comms_purpose ON communications(tenant_id, purpose) WHERE deleted_at IS NULL;
CREATE INDEX idx_comms_initiated ON communications(initiated_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_comms_scheduled ON communications(scheduled_at) WHERE status = 'scheduled' AND deleted_at IS NULL;

-- =============================================================
-- 3. communication_recipients  (per-recipient send record)
-- =============================================================
CREATE TABLE communication_recipients (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  communication_id      UUID NOT NULL REFERENCES communications(id) ON DELETE CASCADE,
  tenant_id             UUID NOT NULL,
  recipient_type        TEXT NOT NULL,                  -- 'student' | 'guardian' | 'staff' | 'external'
  recipient_id          UUID,                           -- FK by type
  guardian_id           UUID,
  student_id            UUID,
  recipient_name        TEXT NOT NULL,
  recipient_contact     TEXT NOT NULL,                  -- email or phone
  channel               communication_channel NOT NULL,
  status                communication_status NOT NULL DEFAULT 'pending',
  sent_at               TIMESTAMPTZ,
  delivered_at          TIMESTAMPTZ,
  read_at               TIMESTAMPTZ,
  replied_at            TIMESTAMPTZ,
  reply_text            TEXT,
  failure_reason        TEXT,
  external_message_id   TEXT,                           -- provider's message ID
  external_status       TEXT,
  cost                  NUMERIC(10,4),
  retry_count           INT NOT NULL DEFAULT 0,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_cr_comm ON communication_recipients(communication_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_cr_tenant_status ON communication_recipients(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_cr_student ON communication_recipients(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_cr_guardian ON communication_recipients(guardian_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_cr_external_id ON communication_recipients(external_message_id) WHERE external_message_id IS NOT NULL;

-- =============================================================
-- 4. sms_outbox  (queue for SMS sending)
-- =============================================================
CREATE TABLE sms_outbox (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  communication_id      UUID REFERENCES communications(id) ON DELETE SET NULL,
  recipient_id          UUID REFERENCES communication_recipients(id) ON DELETE SET NULL,
  to_number             TEXT NOT NULL,
  from_number           TEXT,
  message_body          TEXT NOT NULL,
  segment_count         INT NOT NULL DEFAULT 1,
  provider              sms_provider NOT NULL,
  status                sms_status NOT NULL DEFAULT 'queued',
  scheduled_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  sent_at               TIMESTAMPTZ,
  delivered_at          TIMESTAMPTZ,
  failed_at             TIMESTAMPTZ,
  failure_reason        TEXT,
  external_message_id   TEXT,
  cost                  NUMERIC(10,4),
  retry_count           INT NOT NULL DEFAULT 0,
  last_retry_at         TIMESTAMPTZ,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sms_outbox_tenant_status ON sms_outbox(tenant_id, status) WHERE status = 'queued';
CREATE INDEX idx_sms_outbox_scheduled ON sms_outbox(scheduled_at) WHERE status = 'queued';
CREATE INDEX idx_sms_outbox_external ON sms_outbox(external_message_id) WHERE external_message_id IS NOT NULL;

COMMENT ON TABLE sms_outbox IS 'Outbox queue for SMS. Workers poll for queued rows, send via provider, update status. Partition by month for 1M+ students × multiple SMS/day.';

-- =============================================================
-- 5. home_visits
-- =============================================================
CREATE TABLE home_visits (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  student_id            UUID NOT NULL,
  visitor_user_id       UUID NOT NULL,
  visit_date            DATE NOT NULL,
  start_time            TIME,
  end_time              TIME,
  address_visited       TEXT,
  household_members_met TEXT[],
  purpose               TEXT NOT NULL,
  observations          TEXT,
  agreements_made       TEXT,
  follow_up_actions     TEXT,
  follow_up_due_date    DATE,
  photo_urls            TEXT[],
  consent_obtained      BOOLEAN NOT NULL DEFAULT FALSE,
  safety_check_passed   BOOLEAN NOT NULL DEFAULT TRUE,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_hv_tenant ON home_visits(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_hv_student ON home_visits(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_hv_date ON home_visits(visit_date DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_hv_visitor ON home_visits(visitor_user_id) WHERE deleted_at IS NULL;

-- =============================================================
-- 6. parent_conferences
-- =============================================================
CREATE TABLE parent_conferences (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL,
  school_year_id        UUID NOT NULL,
  student_id            UUID NOT NULL,
  scheduled_date        TIMESTAMPTZ NOT NULL,
  duration_minutes      INT NOT NULL DEFAULT 30,
  location              TEXT,
  meeting_kind          TEXT NOT NULL DEFAULT 'in_person' CHECK (meeting_kind IN ('in_person','video','phone')),
  video_link            TEXT,
  organizer_user_id     UUID NOT NULL,
  invited_guardian_ids  UUID[] NOT NULL DEFAULT '{}',
  attended_guardian_ids UUID[] NOT NULL DEFAULT '{}',
  status                TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled','confirmed','completed','cancelled','no_show','rescheduled')),
  agenda                TEXT,
  discussion_topics     TEXT,
  agreements            TEXT,
  action_items         TEXT,
  follow_up_date        DATE,
  communication_id      UUID,                           -- link to invitation comm
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID,
  updated_by            UUID,
  deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_pc_tenant ON parent_conferences(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_pc_student ON parent_conferences(student_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_pc_date ON parent_conferences(scheduled_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_pc_status ON parent_conferences(tenant_id, status) WHERE deleted_at IS NULL;

-- =============================================================
-- 7. RLS
-- =============================================================
ALTER TABLE communication_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication_templates FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_ct_read ON communication_templates
  FOR SELECT USING (tenant_id IS NULL OR tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_ct_write ON communication_templates
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE communications ENABLE ROW LEVEL SECURITY;
ALTER TABLE communications FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_comms_read ON communications
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_comms_write ON communications
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE communication_recipients ENABLE ROW LEVEL SECURITY;
ALTER TABLE communication_recipients FORCE ROW LEVEL SECURITY;
-- Recipients (guardians) need to see their own comms; the app sets app.current_student_id for parent portal
CREATE POLICY rls_cr_read ON communication_recipients
  FOR SELECT USING (
    tenant_id = core.current_tenant_id() OR core.is_system_admin()
    OR recipient_id::text = COALESCE(NULLIF(current_setting('app.current_user_id', true), ''), '')
  );
CREATE POLICY rls_cr_write ON communication_recipients
  FOR ALL USING (core.current_user_id() IS NOT NULL);

ALTER TABLE sms_outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE sms_outbox FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_sms_read ON sms_outbox
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_sms_write ON sms_outbox
  FOR ALL USING (core.is_system_admin());

ALTER TABLE home_visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE home_visits FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_hv_read ON home_visits
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_hv_write ON home_visits
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

ALTER TABLE parent_conferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE parent_conferences FORCE ROW LEVEL SECURITY;
CREATE POLICY rls_pc_read ON parent_conferences
  FOR SELECT USING (tenant_id = core.current_tenant_id() OR core.is_system_admin());
CREATE POLICY rls_pc_write ON parent_conferences
  FOR ALL USING (core.is_tenant_admin() OR core.current_user_id() IS NOT NULL);

-- =============================================================
-- 8. Triggers
-- =============================================================
DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'communication_templates', 'communications', 'communication_recipients',
    'sms_outbox', 'home_visits', 'parent_conferences'
  ])
  LOOP
    EXECUTE format('
      CREATE TRIGGER tg_set_updated_at BEFORE UPDATE ON comms.%I
        FOR EACH ROW EXECUTE FUNCTION core.tg_set_updated_at();
    ', t);
  END LOOP;
END $$;

-- =============================================================
-- 9. Auto-compute SMS segment count (160 chars per GSM, 70 for Unicode)
-- =============================================================
CREATE OR REPLACE FUNCTION comms.tg_compute_sms_segments() RETURNS TRIGGER AS $$
DECLARE
  v_len INT;
  v_is_unicode BOOLEAN;
BEGIN
  v_len := length(NEW.message_body);
  v_is_unicode := NEW.message_body ~ '[^\x00-\x7F]';
  IF v_is_unicode THEN
    NEW.segment_count := GREATEST(1, CEIL(v_len::NUMERIC / 70));
  ELSE
    NEW.segment_count := GREATEST(1, CEIL(v_len::NUMERIC / 160));
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_compute_sms_segments
  BEFORE INSERT ON comms.sms_outbox
  FOR EACH ROW EXECUTE FUNCTION comms.tg_compute_sms_segments();

-- =============================================================
-- End of Module 8
-- =============================================================
