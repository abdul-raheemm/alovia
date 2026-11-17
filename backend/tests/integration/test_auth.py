"""Token verification (SECURITY.md §1), tested with locally generated keys (no Supabase call)."""

import base64
import hashlib
import hmac
import io
import json
import logging
import time
from collections.abc import Iterator
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.common.responses import ok
from app.core.auth import CurrentUser, get_current_user
from app.core.logging import LOGGER_NAME, JsonFormatter
from app.main import create_app
from tests.helpers import make_settings

ISSUER = "https://example.test/auth/v1"
KID = "test-key"
KEY = ec.generate_private_key(ec.SECP256R1())
OTHER_KEY = ec.generate_private_key(ec.SECP256R1())


def jwks_for(private_key: ec.EllipticCurvePrivateKey, kid: str = KID) -> dict[str, Any]:
    jwk = jwt.algorithms.ECAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    return {"keys": [{**jwk, "kid": kid, "alg": "ES256", "use": "sig"}]}


class FakeJWKClient(jwt.PyJWKClient):
    """Serves a fixed key set instead of fetching it over the network."""

    def __init__(self, jwks: dict[str, Any] | None) -> None:
        super().__init__("https://example.test/jwks")
        self._jwks = jwks

    def fetch_data(self) -> Any:
        if self._jwks is None:
            raise jwt.PyJWKClientConnectionError("unreachable")
        return self._jwks


def claims(**overrides: Any) -> dict[str, Any]:
    now = int(time.time())
    base = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "test.patient@example.test",
        "aud": "authenticated",
        "iss": ISSUER,
        "iat": now,
        "exp": now + 600,
    }
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not None}


def token(key: ec.EllipticCurvePrivateKey = KEY, kid: str = KID, **overrides: Any) -> str:
    return jwt.encode(claims(**overrides), key, algorithm="ES256", headers={"kid": kid})


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def unsigned_token(alg: str, secret: bytes | None = None) -> str:
    """Hand-built token for algorithm-confusion tests (PyJWT refuses to create these)."""
    head = b64(json.dumps({"alg": alg, "typ": "JWT", "kid": KID}).encode())
    body = b64(json.dumps(claims()).encode())
    signing_input = f"{head}.{body}".encode()
    sig = b64(hmac.new(secret, signing_input, hashlib.sha256).digest()) if secret else ""
    return f"{head}.{body}.{sig}"


@pytest.fixture
def app() -> FastAPI:
    app = create_app(make_settings(supabase_jwt_issuer=ISSUER))
    app.state.jwks_client = FakeJWKClient(jwks_for(KEY))

    @app.get("/test/whoami")
    def whoami(user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:  # noqa: B008
        return ok({"id": user.id, "email": user.email})

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def log_buffer(app: FastAPI) -> Iterator[io.StringIO]:
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(JsonFormatter())
    log = logging.getLogger(LOGGER_NAME)
    log.addHandler(handler)
    yield buffer
    log.removeHandler(handler)


def get(client: TestClient, auth: str | None) -> Any:
    return client.get("/test/whoami", headers={"Authorization": auth} if auth else {})


def test_valid_token_accepted(client: TestClient) -> None:
    res = get(client, f"Bearer {token()}")
    assert res.status_code == 200
    assert res.json()["data"] == {
        "id": "11111111-1111-1111-1111-111111111111",
        "email": "test.patient@example.test",
    }


PUBLIC_PEM = KEY.public_key().public_bytes(
    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
)


@pytest.mark.parametrize(
    "auth",
    [
        None,  # no header
        "Basic abc",  # wrong scheme
        "Bearer not-a-token",
        f"Bearer {token(exp=int(time.time()) - 10)}",  # expired
        f"Bearer {token(iss='https://evil.test/auth/v1')}",  # wrong issuer
        f"Bearer {token(aud='anon')}",  # wrong audience
        f"Bearer {token(sub=None)}",  # no subject
        f"Bearer {token(exp=None)}",  # no expiry
        f"Bearer {token(key=OTHER_KEY)}",  # signed with a different key, same kid
        f"Bearer {token(kid='unknown')}",  # key not in the project's key set
        f"Bearer {unsigned_token('none')}",  # alg none
        f"Bearer {unsigned_token('HS256', PUBLIC_PEM)}",  # HS256 signed with the public key
    ],
    ids=[
        "missing",
        "basic",
        "garbage",
        "expired",
        "issuer",
        "audience",
        "no-sub",
        "no-exp",
        "other-key",
        "unknown-kid",
        "alg-none",
        "hs256",
    ],
)
def test_bad_tokens_rejected(client: TestClient, auth: str | None) -> None:
    res = get(client, auth)
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTH_REQUIRED"


def test_key_server_down_is_service_unavailable(app: FastAPI, client: TestClient) -> None:
    app.state.jwks_client = FakeJWKClient(None)
    res = get(client, f"Bearer {token()}")
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_rejection_logged_without_token(client: TestClient, log_buffer: io.StringIO) -> None:
    bad = token(iss="https://evil.test/auth/v1")
    get(client, f"Bearer {bad}")
    text = log_buffer.getvalue()
    assert bad not in text
    assert bad.split(".")[2] not in text  # not even the signature part
    line = next(json.loads(x) for x in text.splitlines() if '"auth rejected"' in x)
    assert line["reason"] == "InvalidIssuerError"
