import json
import logging
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import CONSENT_VERSION, Settings
from app.core.logging import JsonFormatter, request_id_var
from tests.helpers import make_settings


def test_cors_origins_split_from_comma_string() -> None:
    settings = make_settings(cors_origins=" http://a:5173 , http://b:5174,, ")
    assert settings.cors_origins == ["http://a:5173", "http://b:5174"]


def test_defaults_without_env_file() -> None:
    settings = make_settings()
    assert (settings.app_env, settings.log_level, settings.cors_origins) == (
        "development",
        "INFO",
        [],
    )


def test_unknown_app_env_rejected() -> None:
    with pytest.raises(ValidationError):
        make_settings(app_env="staging")


def test_auth_and_database_settings_are_required() -> None:
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None)
    missing = {err["loc"][0] for err in exc.value.errors()}
    assert missing == {"supabase_jwks_url", "supabase_jwt_issuer", "database_url"}


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


def test_consent_version_matches_consent_text() -> None:
    # DEC-031: the backend copy must equal the version written in the legal text
    text = (Path(__file__).resolve().parents[3] / "docs/legal/CONSENT_TEXT.md").read_text("utf-8")
    match = re.search(r"\*\*Consent version:\*\* `([^`]+)`", text)
    assert match, "version line not found in CONSENT_TEXT.md"
    assert match.group(1) == CONSENT_VERSION
