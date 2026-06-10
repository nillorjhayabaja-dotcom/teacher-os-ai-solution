# TeacherOS - Docker Architecture Guide

## Overview

TeacherOS runs as a fully containerized platform with **20+ microservices** orchestrated via Docker Compose. The architecture supports local development, staging, and production environments with a single command: `docker compose up -d`.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        INTERNET (Port 80/443)                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │  teacheros-proxy     │
                         │  (Nginx Reverse Proxy)│
                         │  SSL Termination     │
                         │  Rate Limiting       │
                         │  Compression         │
                         └──────┬─────────┬─────┘
                                │         │
                    ┌───────────▼─┐   ┌───▼────────────┐
                    │ /api, /ws   │   │ / (Frontend)   │
                    │ Backend API │   │  Next.js        │
                    │ FastAPI     │   │  Node.js 22     │
                    │ Port 8000   │   │  Port 3000      │
                    └───────┬─────┘   └─────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
   ┌──────▼──────┐   ┌─────▼──────┐   ┌──────▼────────┐
   │ PostgreSQL  │   │   Redis    │   │ Celery Worker │
   │ PG17+Vector │   │   7.4      │   │ Python 3.12   │
   │ Port 5432   │   │ Port 6379  │   │ AI/PDF/OCR    │
   └─────────────┘   └────────────┘   └──────┬─────────┘
                                             │
                                    ┌────────▼────────┐
                                    │     MinIO       │
                                    │ S3-compatible   │
                                    │ Port 9000       │
                                    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         MONITORING STACK                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐      │
│  │Prometheus│  │ Grafana  │  │   Loki   │  │ OpenTelemetry     │      │
│  │Port 9090 │  │ Port 3001│  │ Port 3100│  │ Collector         │      │
│  └──────────┘  └──────────┘  └──────────┘  │ Port 4317/4318    │      │
│                                             └───────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Service Dependencies

```
teacheros-proxy
  ├── teacheros-frontend (port 3000)
  │     └── teacheros-api (port 8000)
  └── teacheros-api
        ├── teacheros-postgres (port 5432) [health: pg_isready]
        └── teacheros-redis (port 6379) [health: redis-cli ping]

teacheros-worker
  ├── teacheros-postgres
  ├── teacheros-redis
  └── teacheros-storage (port 9000) [health: /minio/health/live]

teacheros-scheduler
  ├── teacheros-postgres
  └── teacheros-redis

teacheros-db-init
  └── teacheros-postgres

teacheros-storage-setup
  └── teacheros-storage

Monitoring Stack:
  teacheros-grafana ──> teacheros-prometheus
  teacheros-prometheus
    ├── teacheros-api (scrapes /metrics)
    ├── teacheros-postgres-exporter
    ├── teacheros-redis-exporter
    └── teacheros-otel-collector
```

## Quick Start

### Prerequisites

- Docker 27+ and Docker Compose v2+
- Git
- Make (optional, for convenience commands)

### Local Development

```bash
# 1. Clone the repository
git clone <repo-url>
cd teacher-os-ai-solution

# 2. Copy environment files
cp .env.example .env.development

# 3. Generate JWT keys (if not existing)
mkdir -p keys
openssl genpkey -algorithm RSA -out keys/private.pem -pkeyopt rsa_keygen_bits:4096
openssl rsa -pubout -in keys/private.pem -out keys/public.pem

# 4. Create data directories
mkdir -p data/{postgres,redis,minio,grafana,prometheus,uploads,logs/{nginx,api,worker},backups,certbot/{conf,www}}

# 5. Start all services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 6. Check status
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps

# 7. View logs
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
```

### Development URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |
| MinIO Console | http://localhost:9001 |
| Mailpit | http://localhost:8025 |
| Adminer | http://localhost:8080 |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |
| Flower (Celery) | http://localhost:5555 |

### Production Deployment

```bash
# 1. Set up environment
cp .env.example .env.production
# Edit .env.production with production values, secrets, etc.

# 2. Initial SSL setup
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot

# 3. Deploy
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. Verify
curl https://teacheros.ph/health
```

### AI Profile

```bash
# Start with local AI (Ollama + Open WebUI)
docker compose --profile ai up -d
```

### Backup Profile

```bash
# Start backup services
docker compose --profile backup up -d
```

## Environment Configuration

### Environment Files

| File | Purpose |
|------|---------|
| `.env.example` | Template with all variables and defaults |
| `.env.development` | Local development settings |
| `.env.staging` | Staging environment settings |
| `.env.production` | Production environment settings |

### Key Configuration Groups

- **Database**: PostgreSQL connection, pool settings
- **Redis**: Connection, DB selection for different concerns
- **JWT**: Authentication configuration, key paths
- **AI**: Provider API keys (OpenAI, Anthropic), local Ollama
- **Storage**: MinIO credentials, bucket names
- **Email**: SMTP configuration
- **Monitoring**: OpenTelemetry endpoints, Prometheus
- **Security**: Rate limiting, CORS, password policy
- **Backup**: S3 bucket, retention policy

## Docker Networks

### Network Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   frontend-network                       │
│  172.20.0.0/16 (Internal: false)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ teacheros-   │  │ teacheros-   │  │ teacheros-   │  │
│  │ proxy        │  │ frontend     │  │ api          │  │
│  └──────────────┘  └──────────────┘  └──────┬───────┘  │
└─────────────────────────────────────────────┼──────────┘
                                              │
┌─────────────────────────────────────────────┼──────────┐
│                backend-network              │          │
│  172.21.0.0/16 (Internal: true)            │          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────▼───────┐ │
│  │  postgres    │  │   redis      │  │   api        │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  worker      │  │  scheduler   │                    │
│  └──────┬───────┘  └──────────────┘                    │
└─────────┼──────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────┐
│                  storage-network                        │
│  172.23.0.0/16 (Internal: true)                        │
│  ┌──────────────┐  ┌──────────────────────────────┐   │
│  │   minio      │  │  worker                      │   │
│  └──────────────┘  └──────────────────────────────┘   │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│                 monitoring-network                      │
│  172.22.0.0/16 (Internal: false)                       │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌────────────┐  │
│  │Prom  │ │Graf  │ │Post  │ │Redis │ │  OTel      │  │
│  │etheus│ │ ana  │ │Exporter│ │Export│ │  Collector │  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └────────────┘  │
│  ┌──────┐ ┌──────┐                                      │
│  │Loki  │ │Promtail│                                     │
│  └──────┘ └──────┘                                      │
└────────────────────────────────────────────────────────┘
```

### Network Isolation Rules

- **frontend-network**: Public-facing, accessible from host. Proxy, frontend, API.
- **backend-network**: Internal only. Database, Redis, workers, API.
- **storage-network**: Internal only. MinIO accessible only from workers and API.
- **monitoring-network**: Semi-public. Exposed for Grafana access if needed.

## Docker Volumes

### Persistent Volumes

| Volume Name | Host Path | Container Mount | Service |
|-------------|-----------|----------------|---------|
| `postgres_data` | `./data/postgres` | `/var/lib/postgresql/data` | PostgreSQL |
| `redis_data` | `./data/redis` | `/data` | Redis |
| `minio_data` | `./data/minio` | `/data` | MinIO |
| `grafana_data` | `./data/grafana` | `/var/lib/grafana` | Grafana |
| `prometheus_data` | `./data/prometheus` | `/prometheus` | Prometheus |
| `uploads_data` | `./data/uploads` | `/app/uploads` | API, Worker |
| `nginx_logs` | `./data/logs/nginx` | `/var/log/nginx` | Proxy |
| `api_logs` | `./data/logs/api` | `/app/logs` | API |
| `worker_logs` | `./data/logs/worker` | `/app/logs` | Worker |
| `backup_data` | `./data/backups` | `/backups` | Backup |

### Data Persistence Strategy

- All stateful services use **bind mounts** for direct host access
- Data survives container restarts, crashes, and updates
- Logs are preserved for debugging and monitoring
- Backups are stored independently for disaster recovery
- Redis uses both RDB snapshots and AOF for durability

## Multi-Stage Builds

### Frontend (Next.js)

```
Base (node:22-alpine)
  │
  ├── Install system deps (python3, make, g++, curl)
  │
  ├── deps
  │   ├── npm ci (all dependencies)
  │   └── Result: node_modules installed
  │
  ├── builder
  │   ├── npm run build
  │   └── Result: dist/ (compiled assets)
  │
  ├── development
  │   ├── npm install
  │   ├── COPY source code
  │   └── CMD: npm run dev (hot reload)
  │
  └── production (FINAL IMAGE: ~150MB)
      ├── FROM node:22-alpine (fresh)
      ├── Install tini + curl
      ├── COPY dist/ from builder
      ├── COPY node_modules from builder
      ├── npm prune --production
      └── CMD: node dist/server/index.js
```

### Backend (FastAPI)

```
Base (python:3.12-slim)
  │
  ├── Install system deps (gcc, g++, libpq-dev, curl)
  │
  ├── deps
  │   ├── pip install -r requirements.txt
  │   └── pip install gunicorn
  │
  ├── development
  │   ├── pip install watchdog pytest-watch
  │   ├── COPY backend/
  │   └── CMD: uvicorn --reload
  │
  └── production (FINAL IMAGE: ~350MB)
      ├── FROM deps (shared dependecies)
      ├── COPY backend/ /app/
      ├── COPY alembic/
      ├── pip uninstall dev packages
      └── CMD: gunicorn + uvicorn workers
```

### Celery Worker

```
Base (python:3.12-slim)
  │
  ├── deps (same as backend)
  │
  ├── development
  │   ├── COPY backend/
  │   └── CMD: celery worker with auto-reload via watchfiles
  │
  └── production
      ├── COPY backend/
      ├── pip uninstall dev packages
      ├── HEALTHCHECK: celery inspect ping
      └── CMD: celery worker optimized
```

## Health Checks

| Service | Command | Interval | Timeout | Retries | Start Period |
|---------|---------|----------|---------|---------|--------------|
| PostgreSQL | `pg_isready -U teacheros -d teacheros` | 10s | 5s | 5 | 30s |
| Redis | `redis-cli ping` | 10s | 5s | 5 | 10s |
| API | `curl -f http://localhost:8000/health` | 30s | 10s | 3 | 60s |
| Frontend | `curl -f http://localhost:3000/health` | 30s | 10s | 3 | 60s |
| Worker | `celery inspect ping` | 30s | 10s | 3 | 60s |
| MinIO | `curl -f http://localhost:9000/minio/health/live` | 30s | 10s | 3 | 30s |
| Prometheus | `wget -q http://localhost:9090/-/ready` | 30s | 10s | 3 | 30s |
| Grafana | `curl -f http://localhost:3000/api/health` | 30s | 10s | 3 | 30s |
| Proxy | `nginx -t` | 60s | 10s | 3 | 10s |

## Database Initialization

The `teacheros-db-init` container handles:

1. **Alembic Migrations**: Runs `alembic upgrade head` to apply schema changes
2. **Admin Seed**: Creates initial super admin account
3. **Role/Permission Seed**: Creates default RBAC roles and permissions
4. **Default Tenant**: Creates the default school tenant

The `teacheros-postgres` container handles:

1. **Extension Installation**: pgvector, uuid-ossp, pgcrypto on first start
2. **Custom Types**: ENUMs for user roles, attendance status, grade types, etc.
3. **Performance Tuning**: PostgreSQL configuration optimizations
4. **Default Schema**: `teacher_os` and `audit` schemas

## Backup Strategy

### Automatic Backups (via Docker profile)

```bash
# Start automated daily backups
docker compose --profile backup up -d

# This starts teacheros-backup-postgres which runs:
# - Daily PostgreSQL dumps (compressed)
# - 30-day retention
# - 4-week retention
# - 3-month retention
```

### Manual Backup Script

```bash
# Full backup (all services)
./docker/scripts/backup.sh

# Database only
./docker/scripts/backup.sh --db-only

# MinIO only
./docker/scripts/backup.sh --storage-only

# List available backups
./docker/scripts/backup.sh --list

# Restore from backup
./docker/scripts/backup.sh --restore ./data/backups/postgres/teacheros_backup_20250101_000000.sql.gz
```

### Cron-based Automated Backups

```bash
# Add to crontab for automated backups
0 2 * * * cd /opt/teacheros && ./docker/scripts/backup.sh --full >> /var/log/teacheros-backup.log 2>&1
```

## Security Hardening

### Container Security

1. **Non-Root Users**: All containers run as non-root (`teacheros` user)
2. **Read-Only Filesystems**: Frontend runs with `read_only: true`
3. **No New Privileges**: `security_opt: no-new-privileges:true`
4. **Secrets Management**: Sensitive values passed via environment files, never hardcoded
5. **Private Networks**: Backend services isolated on internal networks
6. **TMPFS**: Temporary directories mounted as tmpfs (no disk writes)

### Nginx Security Headers

- HSTS (HTTP Strict Transport Security)
- X-Content-Type-Options (nosniff)
- X-Frame-Options (SAMEORIGIN)
- X-XSS-Protection
- Content Security Policy
- Referrer-Policy
- Permissions-Policy
- Cross-Origin-*-Policy headers

### PostgreSQL Security

- SCRAM-SHA-256 authentication
- Custom user (not postgres)
- Isolated on internal network
- Regular backups
- Connection pooling limits

### Redis Security

- Dangerous commands renamed/disabled (FLUSHALL, CONFIG, etc.)
- Optional password protection
- Isolated on internal network
- Memory limits enforced

## Monitoring & Observability

### Metrics Collected

| Category | Metrics |
|----------|---------|
| **API Performance** | Request rate, latency (p50/p95/p99), error rate, active connections |
| **Database Health** | Connections, query duration, cache hit ratio, replication lag |
| **Redis** | Memory usage, hit rate, connected clients, commands per second |
| **Queue Status** | Queue depth, task completion rate, failed tasks, worker count |
| **AI Usage** | Requests per model, tokens consumed, cost estimation, latency |
| **System** | CPU, memory, disk I/O, network I/O per container |

### Grafana Dashboards (pre-configured)

1. **API Performance Dashboard**: Request throughput, latency distribution, error rates
2. **Database Health Dashboard**: Connection pool, query performance, table sizes
3. **Queue Monitoring Dashboard**: Celery worker stats, task completion, failure rates
4. **AI Usage Dashboard**: Model usage, token consumption, estimated costs
5. **System Overview Dashboard**: Container resource usage, host metrics

### Logging Strategy

- **Structured JSON logging** for all services
- **Centralized logging** via Loki + Promtail
- **Correlation IDs** propagated through all services (X-Request-Id)
- **Log rotation** at container level (max 10MB per file, 5 files)
- **Access logs** in JSON format for easy querying

### OpenTelemetry Integration

- **Traces**: Distributed tracing via OTLP exporter to Tempo
- **Metrics**: Prometheus exposition format via OTEL collector
- **Logs**: Correlation IDs link logs to traces
- **Sampling**: Probabilistic sampling (10% in production)

## CI/CD Pipeline

### GitHub Actions Workflow

```
Push/PR to main/develop
        │
        ▼
  ┌──────────┐
  │ Security │── Trivy, Gitleaks
  │  Scan    │
  └─────┬────┘
        │
  ┌─────▼────┐
  │   Lint   │── ESLint, Prettier, Ruff, MyPy
  └─────┬────┘
        │
  ┌─────▼──────┐
  │    Test    │── pytest with PostgreSQL + Redis
  └─────┬──────┘
        │
  ┌─────▼──────┐
  │   Build    │── Docker buildx (multi-arch)
  │   Images   │── Push to GHCR + Docker Hub
  └─────┬──────┘
        │
  ┌─────▼──────┐     ┌──────────────┐
  │   Deploy   │     │    Deploy    │
  │   Staging  │     │  Production  │
  │  (develop) │     │  (tags/v*)  │
  └────────────┘     └──────────────┘
```

### Docker Image Tagging Strategy

| Tag | Source | Example |
|-----|--------|---------|
| `latest` | main branch | `teacheros-api:latest` |
| `develop` | develop branch | `teacheros-api:develop` |
| `vX.Y.Z` | Git tag | `teacheros-api:v1.2.3` |
| `sha-xxxxx` | Commit SHA | `teacheros-api:sha-a1b2c3d` |

## Common Operations

### Start Services

```bash
# Development
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With AI profile
docker compose --profile ai up -d

# Specific service
docker compose up -d teacheros-api teacheros-postgres
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f teacheros-api

# Last 100 lines
docker compose logs --tail=100 teacheros-api

# Since timestamp
docker compose logs --since=10m teacheros-api
```

### Execute Commands in Containers

```bash
# Database shell
docker exec -it teacheros-postgres psql -U teacheros -d teacheros

# Redis CLI
docker exec -it teacheros-redis redis-cli

# Django shell (if using Django)
docker exec -it teacheros-api python manage.py shell

# Run migrations manually
docker exec teacheros-api alembic upgrade head
```

### Restart Services

```bash
# Restart a single service
docker compose restart teacheros-api

# Rebuild and restart
docker compose up -d --build teacheros-api

# Full restart
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart
```

### Cleanup

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data!)
docker compose down -v

# Clean up unused resources
docker system prune -af

# Remove all data
rm -rf data/*
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 80, 443, 3000, 8000, 5432, 6379 are available
2. **Permission denied**: Run `chmod +x docker/scripts/*.sh` for scripts
3. **Docker not running**: Start Docker Desktop or Docker daemon
4. **Missing .env files**: Copy `.env.example` to `.env.development` or `.env.production`
5. **Database not connecting**: Wait for PostgreSQL health check to pass
6. **Hot reload not working**: Ensure `CHOKIDAR_USEPOLLING=true` and `WATCHPACK_POLLING=true` in dev

### Health Check Debugging

```bash
# Check all services health
docker compose ps

# View health check logs
docker inspect --format='{{json .State.Health}}' teacheros-api

# Force health check
docker healthcheck teacheros-api
```

### Reset Everything

```bash
# Complete reset (development)
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
rm -rf data/*
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## Best Practices

1. **Never commit .env files with real secrets** to version control
2. **Use Docker Compose profiles** to start only needed services
3. **Regularly prune unused Docker resources**: `docker system prune -af`
4. **Monitor disk usage**: All data volumes are in `./data/`
5. **Keep Docker and Docker Compose updated**
6. **Use `.env.development`** for local work, never modify `.env.example`
7. **Run security scans** before deploying to production
8. **Test backups** regularly by performing test restores
9. **Pin service versions** in docker-compose.yml for reproducibility
10. **Use multi-stage builds** to minimize production image sizes

## Directory Structure

```
teacher-os-ai-solution/
├── .env.example              # Environment template
├── .env.development          # Local development env
├── .env.staging              # Staging env
├── .env.production           # Production env
├── docker-compose.yml        # Main orchestration
├── docker-compose.dev.yml    # Development overrides
├── docker-compose.prod.yml   # Production overrides
├── docker/
│   ├── frontend/
│   │   └── Dockerfile        # Multi-stage frontend build
│   ├── backend/
│   │   └── Dockerfile        # Multi-stage backend build
│   ├── celery/
│   │   └── Dockerfile        # Celery worker build
│   └── scripts/
│       ├── backup.sh         # Backup script
│       └── setup.sh          # Initial setup script
├── infra/
│   ├── nginx/
│   │   ├── nginx.conf        # Production Nginx config
│   │   └── security-headers.conf
│   ├── postgres/
│   │   ├── init.sql          # DB initialization
│   │   └── postgresql.conf   # Production DB config
│   ├── redis/
│   │   └── redis.conf        # Redis configuration
│   └── monitoring/
│       ├── prometheus/
│       │   └── prometheus.yml
│       ├── grafana/
│       │   └── provisioning/
│       │       ├── datasources/
│       │       └── dashboards/
│       ├── otel-collector.yml
│       └── loki.yml
├── data/                     # Runtime data (gitignored)
│   ├── postgres/
│   ├── redis/
│   ├── minio/
│   ├── grafana/
│   ├── prometheus/
│   ├── uploads/
│   ├── logs/
│   ├── backups/
│   └── certbot/
├── .github/
│   └── workflows/
│       └── ci-cd.yml         # GitHub Actions pipeline
├── frontend/                 # Frontend source code
├── backend/                  # Backend source code
└── keys/                     # JWT keys (gitignored)
    ├── private.pem
    └── public.pem
```

## Performance Tuning

### PostgreSQL

- `shared_buffers`: 256MB (container default)
- `effective_cache_size`: 768MB
- `work_mem`: 16MB per operation
- `maintenance_work_mem`: 64MB
- `max_connections`: 200
- `random_page_cost`: 1.1 (SSD optimization)

### Gunicorn Workers

- Formula: `(2 × CPU cores) + 1`
- Default: 4 workers
- UvicornWorker for ASGI support
- Max requests: 10000 per worker

### Redis

- `maxmemory`: 512MB
- `maxmemory-policy`: allkeys-lru
- AOF + RDB persistence
- 16 databases for isolation

### Nginx

- Worker connections: 10240
- Gzip compression enabled
- Static asset caching (30 days)
- Rate limiting zones configured

## Scaling

### Vertical Scaling (Single Server)

Increase resources in `docker-compose.prod.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
```

### Horizontal Scaling (Multiple Workers)

```yaml
teacheros-worker:
  deploy:
    mode: replicated
    replicas: 3
```

### Future: Docker Swarm / Kubernetes

The docker-compose files are structured with `deploy` sections ready for Docker Swarm mode or can be converted to Kubernetes manifests with tools like `kompose`.