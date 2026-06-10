# TODO - TeacherOS backend platform build

## Phase 1: Fix scaffolding & imports
- [x] Make missing package re-exports optional in `backend/src/*/__init__.py` to prevent Pylance missing-import failures.

## Phase 2: Foundational platform layer (no business domains)
- [x] Implement FastAPI application bootstrap + router mounting
- [x] Implement Authentication platform (RefreshTokenService, PasswordService, AuthMiddleware)
- [x] Implement Authorization platform (RBAC, Role Engine, Permission Engine)
- [x] Implement Workflow runtime (WorkflowState/Transition/History/Engine/Executor)
- [x] Implement persistent EventStore + EventReplay backed by DB
- [x] Implement WebSocket framework (ConnectionManager + channels)
- [x] Implement Celery infrastructure (celery app, queue manager, retry + DLQ wiring)
- [x] Implement Observability (structured logging, Prometheus metrics, OpenTelemetry tracing, health endpoints)

- [x] Add platform-only tests (auth, RBAC, workflow, event store, websocket)


