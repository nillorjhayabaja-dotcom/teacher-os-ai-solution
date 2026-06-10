from __future__ import annotations

from backend.src.infrastructure.message_queue.celery_app import celery_app


@celery_app.task(name="tasks.form_generate.generate_sf2")
def generate_sf2(school_id: str | None = None, quarter: str | None = None) -> dict:
    return {"status": "queued", "school_id": school_id, "quarter": quarter}

