# =============================================================================
# TeacherOS - Celery Worker Dockerfile
# =============================================================================
# Stage 1: Base dependencies
# Stage 2: Development
# Stage 3: Production
# =============================================================================

# =============================================================================
# Stage 1: Base
# =============================================================================
FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r teacheros && useradd -r -g teacheros -d /app -s /bin/bash teacheros

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
        gunicorn==22.0.0 \
        flower==2.0.1

# =============================================================================
# Stage 2: Development
# =============================================================================
FROM base AS development

COPY backend/ /app/

USER teacheros

# Celery worker with auto-reload
CMD ["celery", "-A", "backend.src.tasks.celery_app", "worker", \
    "--loglevel=info", \
    "--concurrency=4", \
    "--max-tasks-per-child=100", \
    "--max-memory-per-child=150000", \
    "--time-limit=3600", \
    "--soft-time-limit=3000", \
    "--autoscale=10,4", \
    "--pool=prefork", \
    "--uid=teacheros", \
    "--events", \
    "--task-events", \
    "--without-gossip", \
    "--without-mingle"]

# =============================================================================
# Stage 3: Production
# =============================================================================
FROM base AS production

COPY backend/ /app/

RUN mkdir -p /app/logs && chown -R teacheros:teacheros /app

RUN pip uninstall -y pytest pytest-asyncio pytest-cov coverage mypy ruff 2>/dev/null || true && \
    rm -rf /root/.cache/pip /tmp/*

USER teacheros

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD celery -A backend.src.tasks.celery_app inspect ping || exit 1

# Celery worker - production optimized
CMD ["celery", "-A", "backend.src.tasks.celery_app", "worker", \
    "--loglevel=info", \
    "--concurrency=8", \
    "--max-tasks-per-child=1000", \
    "--max-memory-per-child=200000", \
    "--time-limit=3600", \
    "--soft-time-limit=3000", \
    "--autoscale=16,4", \
    "--pool=prefork", \
    "--uid=teacheros", \
    "--events", \
    "--task-events", \
    "--without-gossip", \
    "--without-mingle"]