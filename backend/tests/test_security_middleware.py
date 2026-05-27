from fastapi import FastAPI
from fastapi.testclient import TestClient

from middleware.security import configure_security_middleware


class DummySettings:
    SECURITY_CSP = "default-src 'self'; frame-ancestors 'none'"
    REQUEST_MAX_BODY_SIZE_BYTES = 8

    def allowed_origins_list(self):
        return ["https://shadiro.com", "https://www.shadiro.com", "http://localhost:3000"]


def build_app():
    app = FastAPI()

    @app.get("/api/ping")
    async def ping():
        return {"ok": True}

    @app.post("/api/echo")
    async def echo(payload: dict):
        return payload

    configure_security_middleware(app, DummySettings())
    return app


def test_security_headers_are_applied():
    client = TestClient(build_app())
    response = client.get("/api/ping")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "strict-transport-security" in response.headers
    assert "content-security-policy" in response.headers


def test_request_size_limit_returns_json_error():
    client = TestClient(build_app())
    response = client.post("/api/echo", content='{"payload":"too-large"}', headers={"content-type": "application/json"})

    assert response.status_code == 413
    assert response.json()["success"] is False
    assert response.json()["error_code"] == "PAYLOAD_TOO_LARGE"


def test_cors_rejects_unconfigured_origin():
    client = TestClient(build_app())
    response = client.options(
        "/api/ping",
        headers={
            "origin": "https://evil.example",
            "access-control-request-method": "GET",
        },
    )

    assert response.status_code == 400
    assert response.headers.get("access-control-allow-origin") != "*"
