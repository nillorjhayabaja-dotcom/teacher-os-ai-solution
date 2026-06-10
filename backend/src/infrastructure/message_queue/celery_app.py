from __future__ import annotations

"""Celery application instance.

Foundational platform scaffold.

Note: this repository phase focuses on code organization and interfaces.
Actual broker/backend URLs should be provided via environment variables.
"""

from celery import Celery

from backend.src.core.settings import settings


def _build_app() -> Celery:
    # Uses Redis as broker/back-end by default (matches architecture).
    return Celery(
        "teacheros",
        broker=str(settings.REDIS_URL).replace("redis://", "redis://"),
        backend=str(settings.REDIS_URL).replace("redis://", "redis://"),
        include=[
            "backend.src.tasks.grade_compute",
            "backend.src.tasks.form_generate",
            "backend.src.tasks.ai_generation",
            "backend.src.tasks.ocr_processing",
        ],
    )


celery_app = _build_app()


__all__ = ["celery_app"]
