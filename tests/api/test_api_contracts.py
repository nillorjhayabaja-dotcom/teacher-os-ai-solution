from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from httpx import AsyncClient

from backend.src.api.v1.ai.agents import router as ai_agents_router
from backend.src.main import create_app


@pytest.fixture
def app():
    app = create_app()
    if not any(getattr(route, "path", "") == "/api/v1/ai/agents" for route in app.routes):
        app.include_router(ai_agents_router)
    return app


@pytest.mark.api
@pytest.mark.contract
@pytest.mark.asyncio
async def test_health_endpoint_contract(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.api
@pytest.mark.contract
@pytest.mark.asyncio
async def test_ai_agents_list_contract(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/ai/agents")
    body = response.json()
    assert response.status_code == 200
    assert body["total"] >= 7
    assert {"kind", "name", "description", "default_model", "required_tools"}.issubset(body["agents"][0])


@pytest.mark.api
@pytest.mark.contract
@pytest.mark.asyncio
async def test_ai_agent_detail_and_not_found_contract(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        ok = await client.get("/api/v1/ai/agents/lesson_planning")
        missing = await client.get("/api/v1/ai/agents/unknown")
    assert ok.status_code == 200
    assert ok.json()["output_schema"]["type"] == "object"
    assert missing.status_code == 404


@pytest.mark.api
@pytest.mark.contract
@pytest.mark.asyncio
async def test_ai_agent_run_request_validation_and_response_contract(app, tenant_id, user_id):
    payload = {
        "domain_data": {"subject": "Science", "grade_level": "6", "topic": "Matter"},
        "context": {"tenant_id": str(tenant_id), "user_id": str(user_id)},
    }
    invalid = {"domain_data": {"topic": "Matter"}, "temperature_override": 3}
    async with AsyncClient(app=app, base_url="http://test") as client:
        ok = await client.post("/api/v1/ai/agents/lesson_planning/run", json=payload)
        bad = await client.post("/api/v1/ai/agents/lesson_planning/run", json=invalid)

    assert ok.status_code == 200
    assert ok.json()["status"] == "completed"
    assert {"run_id", "status", "agent_kind", "token_usage"}.issubset(ok.json())
    assert bad.status_code == 422


@pytest.mark.api
@pytest.mark.contract
def test_openapi_contains_versioned_core_paths(app):
    schema = app.openapi()
    assert "/health" in schema["paths"]
    assert "/api/v1/auth/login" in schema["paths"]
    assert "/api/v1/users/me" in schema["paths"]
    assert "/api/v1/ai/agents" in schema["paths"]


@pytest.mark.api
@pytest.mark.xfail_architecture_gap(reason="Most domain REST endpoints from ARCHITECTURE.md are not implemented yet.")
def test_all_documented_domain_endpoints_exist(app):
    paths = app.openapi()["paths"]
    for expected in [
        "/api/v1/students",
        "/api/v1/lessons",
        "/api/v1/assessments",
        "/api/v1/gradebook",
        "/api/v1/forms",
        "/api/v1/reports",
    ]:
        assert expected in paths


@pytest.mark.api
@pytest.mark.contract
@pytest.mark.xfail_architecture_gap(reason="Pagination/filtering/sorting/search contract is documented but not implemented on scaffold endpoints.")
def test_collection_endpoints_expose_pagination_filtering_sorting_and_search(app):
    params = app.openapi()["paths"]["/api/v1/students"]["get"]["parameters"]
    names = {p["name"] for p in params}
    assert {"page", "page_size", "filter", "sort", "q"}.issubset(names)
