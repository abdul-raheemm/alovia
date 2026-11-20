"""Private Supabase Storage bucket for medical records (Dashboard spec §14, SECURITY.md §8).

Only the backend talks to Storage, with the service-role key from backend/.env (never sent to
a browser, never logged). Downloads are short-lived signed links. Plain urllib, no SDK
(DEC-078). Tests swap `app.state.storage` for a fake, so they never reach a real bucket.
"""

import json
import urllib.error
import urllib.request
from typing import Protocol
from urllib.parse import quote

from app.core.errors import AppError
from app.core.logging import logger

TIMEOUT_SECONDS = 20


class Storage(Protocol):
    def upload(self, path: str, data: bytes, content_type: str) -> None: ...

    def signed_url(self, path: str, seconds: int) -> str: ...


def _unavailable(reason: str) -> AppError:
    logger.error("storage failed", extra={"reason": reason})  # never the key or the file
    return AppError("SERVICE_UNAVAILABLE", "File storage is not available right now.", status=503)


class SupabaseStorage:
    def __init__(self, url: str | None, service_key: str | None, bucket: str | None) -> None:
        self._url = (url or "").rstrip("/")
        self._key = service_key or ""
        self._bucket = bucket or ""

    def _request(self, method: str, path: str, body: bytes, content_type: str) -> bytes:
        if not (self._url and self._key and self._bucket):
            raise _unavailable("storage not configured")
        req = urllib.request.Request(
            f"{self._url}/storage/v1/object/{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self._key}",
                "apikey": self._key,
                "Content-Type": content_type,
                "x-upsert": "false",  # a stored file is never replaced
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as res:
                data: bytes = res.read()
                return data
        except urllib.error.HTTPError as exc:
            exc.close()  # the error holds the open response; release it
            raise _unavailable(f"http {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise _unavailable(type(exc).__name__) from exc

    def upload(self, path: str, data: bytes, content_type: str) -> None:
        self._request("POST", f"{self._bucket}/{quote(path)}", data, content_type)

    def signed_url(self, path: str, seconds: int) -> str:
        body = json.dumps({"expiresIn": seconds}).encode()
        out = json.loads(
            self._request("POST", f"sign/{self._bucket}/{quote(path)}", body, "application/json")
        )
        signed = out.get("signedURL") or out.get("signedUrl")
        if not isinstance(signed, str):
            raise _unavailable("no signed url in reply")
        return f"{self._url}/storage/v1{signed}"
