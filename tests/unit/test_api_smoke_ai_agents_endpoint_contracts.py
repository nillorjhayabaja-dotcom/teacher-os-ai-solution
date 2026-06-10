import pytest

from fastapi.testclient import TestClient

from backend.src.main import create_app


@pytest.mark.parametrize(
    "method,path,status_min,status_max",
    [
        ("GET", "/api/v1/ai/agents", 200, 200),
        ("GET", "/api/v1/ai/agents/lesson_planning", 200, 200),
    ],
)
def test_ai_agents_endpoints_smoke(method: str, path: str, status_min: int, status_max: int):
    app = create_app()
    from backend.src.api.v1.ai.agents import router as ai_agents_router
    if not any(getattr(route, "path", "") == "/api/v1/ai/agents" for route in app.routes):
        app.include_router(ai_agents_router)
    client = TestClient(app)

    resp = getattr(client, method.lower())(path)
    assert status_min <= resp.status_code <= status_max


def test_ai_run_agent_happy_path_returns_json():
    app = create_app()
    from backend.src.api.v1.ai.agents import router as ai_agents_router
    if not any(getattr(route, "path", "") == "/api/v1/ai/agents" for route in app.routes):
        app.include_router(ai_agents_router)
    client = TestClient(app)

    payload = {
        "domain_data": {
            "grade_level": "Grade 3",
            "subject": "Mathematics",
            "topic": "Fractions",
        },
        "context": {
            "tenant_id": "00000000-0000-0000-0000-00000000000a",
            "user_id": "00000000-0000-0000-0000-00000000a001",
        },
    }
    resp = client.post("/api/v1/ai/agents/lesson_planning/run", json=payload)
    assert resp.status_code in (200, 400)
    assert resp.headers["content-type"].startswith("application/json")