"""Infrastructure layer – integrations with external services.

Exports the database engine, Redis client and Celery application instance.
"""

from .database import engine, Base  # noqa: F401

try:
    from .redis_client import redis_client  # type: ignore # noqa: F401
except ImportError:  # pragma: no cover
    # Optional re-export; integration may be added later.
    pass

# Celery app lives under infrastructure/message_queue in this scaffold.
try:
    from .message_queue.celery_app import celery_app  # type: ignore # noqa: F401
except ImportError:  # pragma: no cover
    pass


