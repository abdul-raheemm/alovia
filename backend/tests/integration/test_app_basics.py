"""Envelope, error handling, request ID and /health (docs/API.md §2-3, OBSERVABILITY.md)."""

import io
import json
import logging
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import AppError
from app.core.logging import LOGGER_NAME, JsonFormatter
from app.main import create_app

ORIGIN = "http://localhost:5173"
AUTH: dict[str, Any] = {
    "supabase_jwks_url": "https://example.test/auth/v1/.well-known/jwks.json",
    "supabase_jwt_issuer": "https://example.test/auth/v1",
}


@pytest.fixture
def app() -> FastAPI:
    app = create_app(Settings(_env_file=None, cors_origins=ORIGIN, **AUTH))

    # test-only routes, to exercise the error paths
    @app.get("/test/app-error")
    def app_error() -> None:
        raise AppError("CONFLICT", "Already used.", status=409, fields={"code": "E1"})

    @app.get("/test/crash")
    def crash() -> None:
        raise RuntimeError("secret internal detail")

    @app.get("/test/needs-int")
    def needs_int(n: int) -> dict[str, int]:
        return {"n": n}

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {
        "data": {
            "status": "ok",
            "models_loaded": False,
            "rules_loaded": {"genetic": False, "symptoms": False, "journey": False},
            "version": "0.0.0",
        },
        "error": None,
    }
    assert len(res.headers["X-Request-ID"]) == 32


def test_unknown_route_is_not_found_envelope(client: TestClient) -> None:
    res = client.get("/api/v1/nope")
    assert res.status_code == 404
    assert res.json()["data"] is None
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_validation_error_lists_fields(client: TestClient) -> None:
    res = client.get("/test/needs-int", params={"n": "abc"})
    assert res.status_code == 400
    error = res.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert set(error["fields"]) == {"n"}


def test_app_error_keeps_code_status_and_fields(client: TestClient) -> None:
    res = client.get("/test/app-error")
    assert res.status_code == 409
    assert res.json() == {
        "data": None,
        "error": {"code": "CONFLICT", "message": "Already used.", "fields": {"code": "E1"}},
    }


@pytest.fixture
def log_buffer(app: FastAPI) -> Iterator[io.StringIO]:
    """Collect the app's JSON log lines in memory (pytest swaps stdout between test phases)."""
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(JsonFormatter())
    log = logging.getLogger(LOGGER_NAME)
    log.addHandler(handler)
    yield buffer
    log.removeHandler(handler)


def lines(buffer: io.StringIO) -> list[dict[str, Any]]:
    return [json.loads(line) for line in buffer.getvalue().splitlines()]


def test_crash_returns_internal_error_without_details(
    client: TestClient, log_buffer: io.StringIO
) -> None:
    res = client.get("/test/crash")
    assert res.status_code == 500
    assert res.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "secret internal detail" not in res.text
    assert "X-Request-ID" in res.headers
    # the detail goes to the server log, with the same request ID
    crash_line = next(line for line in lines(log_buffer) if line["message"] == "unhandled error")
    assert "secret internal detail" in crash_line["exc"]
    assert crash_line["request_id"] == res.headers["X-Request-ID"]


def test_request_log_line(client: TestClient, log_buffer: io.StringIO) -> None:
    res = client.get("/api/v1/health")
    req = next(line for line in lines(log_buffer) if line["message"] == "request")
    assert req["request_id"] == res.headers["X-Request-ID"]
    assert (req["method"], req["path"], req["status"]) == ("GET", "/api/v1/health", 200)


def test_cors_allows_configured_origin_only(client: TestClient) -> None:
    allowed = client.get("/api/v1/health", headers={"Origin": ORIGIN})
    other = client.get("/api/v1/health", headers={"Origin": "http://evil.example"})
    assert allowed.headers["access-control-allow-origin"] == ORIGIN
    assert "access-control-allow-origin" not in other.headers
