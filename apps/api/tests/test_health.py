import asyncio
import json

from fastapi.testclient import TestClient
from starlette.requests import Request

from margin_api.main import app, handle_unexpected_error


def test_health_returns_stable_public_response() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "openrouter" not in response.text.lower()


def test_unknown_route_uses_stable_error_shape() -> None:
    with TestClient(app) as client:
        response = client.get("/api/not-a-route")

    assert response.status_code == 404
    assert response.json() == {
        "code": "not_found",
        "message": "The requested resource was not found.",
        "retryable": False,
    }


def test_unexpected_error_uses_stable_shape_without_leaking_details() -> None:
    request = Request({"type": "http", "method": "GET", "path": "/api/test", "headers": []})

    assert app.exception_handlers[Exception] is handle_unexpected_error
    response = asyncio.run(handle_unexpected_error(request, RuntimeError("sensitive detail")))

    assert response.status_code == 500
    assert json.loads(response.body) == {
        "code": "internal_server_error",
        "message": "The server encountered an unexpected error.",
        "retryable": True,
    }
    assert b"sensitive detail" not in response.body
