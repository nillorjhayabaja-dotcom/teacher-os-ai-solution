from __future__ import annotations

from backend.src.infrastructure.message_queue.celery_app import celery_app


@celery_app.task(name="tasks.grade_compute.compute_grades")
def compute_grades(school_year_id: str | None = None, period: str | None = None) -> dict:
    # Foundational stub.
    return {"status": "queued", "school_year_id": school_year_id, "period": period}

