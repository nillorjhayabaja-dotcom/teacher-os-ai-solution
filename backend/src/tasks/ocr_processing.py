from __future__ import annotations

from backend.src.infrastructure.message_queue.celery_app import celery_app


@celery_app.task(name="tasks.ocr_processing.process_upload")
def process_upload(file_id: str) -> dict:
    return {"status": "queued", "file_id": file_id}

