# =============================================================================
# TeacherOS - Backend API Dockerfile (Multi-stage)
# =============================================================================
# Stage 1: Python dependencies
# Stage 2: Build stage (if needed for compiled extensions)
# Stage 3: Development Runtime
# Stage 4: Production Runtime
# =============================================================================

# =============================================================================
# Stage 1: Base - Python 3.12 slim
# =============================================================================
FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r teacheros && useradd -r -g teacheros -d /app -s /bin/bash teacheros

WORKDIR /app

# =============================================================================
# Stage 2: Dependencies - Install Python packages
# =============================================================================
FROM base AS deps

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn==22.0.0

# =============================================================================
# Stage 3: Development Runtime - Hot reload with Uvicorn
# =============================================================================
FROM base AS development

# Install dev dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt && \
    pip install --no-cache-dir \
        gunicorn==22.0.0 \
        watchdog[watchmedo]==4.0.1 \
        pytest-watch==4.2.0

# Copy source code
COPY backend/ /app/

# Set user
USER teacheros

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start with auto-reload for development
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app"]

# =============================================================================
# Stage 4: Production Runtime - Gunicorn + Uvicorn workers
# =============================================================================
FROM deps AS production

# Copy source code
COPY backend/ /app/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini

# Create necessary directories
RUN mkdir -p /app/keys /app/logs /app/uploads && \
    chown -R teacheros:teacheros /app

# Remove dev dependencies and cache
RUN pip uninstall -y pytest pytest-asyncio pytest-cov coverage mypy ruff freezegun testcontainers 2>/dev/null || true && \
    rm -rf /root/.cache/pip /tmp/*

# Set to non-root user
USER teacheros

# Security: restrict permissions
RUN chmod 755 /app && \
    chmod 700 /app/keys

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start with Gunicorn + Uvicorn workers for production
# Workers = 2 * CPU cores + 1
# Using UvicornWorker for ASGI support
CMD ["gunicorn", "backend.src.main:app", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--threads", "2", \
    "--worker-connections", "1000", \
    "--max-requests", "10000", \
    "--max-requests-jitter", "1000", \
    "--timeout", "120", \
    "--keep-alive", "5", \
    "--log-level", "info", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--access-logformat", "%({x-request-id}o)s %(h)s %(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\" %(L)s"]