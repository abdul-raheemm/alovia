"""Supabase Auth admin calls (Dashboard spec §21 "Invite a doctor by email", DEC-101).

Only the backend calls this, with the service-role key (never sent to a browser, never
logged). Supabase sends the invite email; its link opens the doctor app's Set password page.
Plain urllib (DEC-078). Tests swap `app.state.auth_admin` for a fake.
"""

import json
import urllib.error
import urllib.request
from typing import Protocol
from urllib.parse import quote

from app.core.errors import AppError
from app.core.logging import logger

TIMEOUT_SECONDS = 20


class AuthAdmin(Protocol):
    def invite(self, email: str, redirect_to: str) -> str:
        """Send the invite email; return the new Supabase user id."""
        ...


class SupabaseAuthAdmin:
    def __init__(self, url: str | None, service_key: str | None) -> None:
        self._url = (url or "").rstrip("/")
        self._key = service_key or ""

    def invite(self, email: str, redirect_to: str) -> str:
        if not (self._url and self._key):
            logger.error("auth admin failed", extra={"reason": "not configured"})
            raise AppError("SERVICE_UNAVAILABLE", "Invites are not available right now.", 503)
        req = urllib.request.Request(
            f"{self._url}/auth/v1/invite?redirect_to={quote(redirect_to, safe='')}",
            data=json.dumps({"email": email}).encode(),
            method="POST",
            headers={
                "Authorization": f"Bearer {self._key}",
                "apikey": self._key,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as res:
                user_id = json.loads(res.read()).get("id")
        except urllib.error.HTTPError as exc:
            exc.close()
            logger.error("auth admin failed", extra={"reason": f"http {exc.code}"})
            if exc.code == 422:  # Supabase: a user with this email is already registered
                raise AppError(
                    "CONFLICT", "An account with this email already exists.", status=409
                ) from exc
            raise AppError(
                "SERVICE_UNAVAILABLE", "Invites are not available right now.", 503
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            logger.error("auth admin failed", extra={"reason": type(exc).__name__})
            raise AppError(
                "SERVICE_UNAVAILABLE", "Invites are not available right now.", 503
            ) from exc
        if not isinstance(user_id, str):
            logger.error("auth admin failed", extra={"reason": "no user id in reply"})
            raise AppError("SERVICE_UNAVAILABLE", "Invites are not available right now.", 503)
        return user_id


def create_user(url: str | None, service_key: str | None, email: str, password: str) -> str:
    """Development seed only (scripts/seed_dev.py): a confirmed email + password login through
    the Supabase admin API. Returns the new user id. Never called by the running app."""
    if not (url and service_key):
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are needed in .env")
    req = urllib.request.Request(
        f"{url.rstrip('/')}/auth/v1/admin/users",
        data=json.dumps({"email": email, "password": password, "email_confirm": True}).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as res:
            return str(json.loads(res.read())["id"])
    except urllib.error.HTTPError as exc:
        exc.close()
        if exc.code == 422:  # Supabase: the email is already registered
            raise RuntimeError(
                f"{email} already has a Supabase login: run docs/review/reset_seed_data.sql "
                "in Supabase, then run the seed again"
            ) from exc
        raise RuntimeError(f"Supabase refused to create {email} (HTTP {exc.code})") from exc
