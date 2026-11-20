"""The Storage client (Dashboard §14, DEC-078): service key only in headers, signed links built
from Supabase's reply, failures become 503 without any secret in the error."""

import io
import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from app.core.errors import AppError
from app.core.storage import SupabaseStorage


class Reply(io.BytesIO):
    def __enter__(self) -> Reply:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def test_unconfigured_storage_answers_503() -> None:
    with pytest.raises(AppError) as err:
        SupabaseStorage(None, None, None).upload("p/x.pdf", b"%PDF", "application/pdf")
    assert err.value.status == 503


def test_upload_and_signed_url_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[urllib.request.Request] = []

    def fake_urlopen(req: urllib.request.Request, timeout: int) -> Reply:
        sent.append(req)
        if "/sign/" in req.full_url:
            return Reply(json.dumps({"signedURL": "/object/sign/records/p/x.pdf?token=t"}).encode())
        return Reply(b"{}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    store = SupabaseStorage("https://proj.example.test/", "service-key", "records")
    store.upload("patients/1/a b.pdf", b"%PDF", "application/pdf")
    url = store.signed_url("patients/1/a b.pdf", 300)

    up, sign = sent
    assert up.full_url == "https://proj.example.test/storage/v1/object/records/patients/1/a%20b.pdf"
    assert up.get_method() == "POST" and up.get_header("X-upsert") == "false"
    assert up.get_header("Authorization") == "Bearer service-key"
    assert isinstance(sign.data, bytes) and json.loads(sign.data) == {"expiresIn": 300}
    assert url == "https://proj.example.test/storage/v1/object/sign/records/p/x.pdf?token=t"


def test_http_errors_become_503_without_the_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing(req: urllib.request.Request, timeout: int) -> Any:
        raise urllib.error.HTTPError(req.full_url, 400, "bad", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(urllib.request, "urlopen", failing)
    with pytest.raises(AppError) as err:
        SupabaseStorage("https://p.example.test", "secret-key", "b").signed_url("x", 60)
    assert err.value.status == 503 and "secret-key" not in str(err.value.message)
