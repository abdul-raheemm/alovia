import json
import logging
from typing import Any

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.logging import JsonFormatter, request_id_var

AUTH: dict[str, Any] = {
    "supabase_jwks_url": "https://example.test/auth/v1/.well-known/jwks.json",
    "supabase_jwt_issuer": "https://example.test/auth/v1",
}


def test_cors_origins_split_from_comma_string() -> None:
    settings = Settings(_env_file=None, cors_origins=" http://a:5173 , http://b:5174,, ", **AUTH)
    assert settings.cors_origins == ["http://a:5173", "http://b:5174"]


def test_defaults_without_env_file() -> None:
    settings = Settings(_env_file=None, **AUTH)
    assert (settings.app_env, settings.log_level, settings.cors_origins) == (
        "development",
        "INFO",
        [],
    )


def test_unknown_app_env_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="staging", **AUTH)


def test_auth_settings_are_required() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_json_formatter_includes_request_id_and_extras() -> None:
    token = request_id_var.set("abc123")
    try:
        record = logging.LogRecord("alovia", logging.INFO, __file__, 1, "request", None, None)
        record.status = 200
        line = json.loads(JsonFormatter().format(record))
    finally:
        request_id_var.reset(token)
    assert line["request_id"] == "abc123"
    assert line["message"] == "request"
    assert line["status"] == 200
