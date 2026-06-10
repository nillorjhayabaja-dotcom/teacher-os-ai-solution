from __future__ import annotations

import pytest

from backend.src.tasks.form_generate import generate_sf2
from backend.src.tasks.grade_compute import compute_grades
from backend.src.tasks.ocr_processing import process_upload


@pytest.mark.integration
def test_sql_architecture_files_define_multi_tenant_rls_and_audit_tables():
    auth_sql = open("architecture/01-auth-organization.sql", encoding="utf-8").read().lower()
    audit_sql = open("architecture/14-audit-security.sql", encoding="utf-8").read().lower()
    rls_sql = open("architecture/15-17-rls-indexes-mv.sql", encoding="utf-8").read().lower()

    assert "tenant" in auth_sql or "organization" in auth_sql
    assert "audit_logs" in audit_sql
    assert "rls" in rls_sql and "polic" in rls_sql


@pytest.mark.celery
@pytest.mark.integration
def test_celery_stub_tasks_are_importable_and_return_queue_status():
    assert compute_grades.run(school_year_id="sy", period="q1")["status"] == "queued"
    assert generate_sf2.run(school_id="school", quarter="q1")["status"] == "queued"
    assert process_upload.run(file_id="file-1")["file_id"] == "file-1"


@pytest.mark.integration
@pytest.mark.xfail_architecture_gap(reason="Testcontainers-based PostgreSQL/Redis wiring and migrations are not present in the scaffold yet.")
def test_postgres_and_redis_operations_with_testcontainers():
    from testcontainers.postgres import PostgresContainer
    from testcontainers.redis import RedisContainer

    with PostgresContainer("postgres:15-alpine") as postgres, RedisContainer("redis:7-alpine") as redis:
        assert postgres.get_connection_url()
        assert redis.get_connection_url()


@pytest.mark.document_pipeline
@pytest.mark.xfail_architecture_gap(reason="PDF/Word/Excel upload, OCR extraction, storage, retries, and AI analysis pipeline are not implemented yet.")
def test_document_pipeline_upload_ocr_extract_analyze_and_persist():
    assert False, "Document pipeline services/endpoints must exist before executable processing assertions can pass."


@pytest.mark.celery
@pytest.mark.xfail_architecture_gap(reason="Dead letter queues and task recovery policy are not modeled in current Celery scaffold.")
def test_celery_retries_dead_letter_and_recovery_policy_are_configured():
    from backend.src.infrastructure.message_queue.celery_app import celery_app

    assert celery_app.conf.task_routes["*"]["dead_letter_exchange"]
