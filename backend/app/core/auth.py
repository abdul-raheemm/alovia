"""Verify the Supabase access token on every protected request (SECURITY.md §0-1).

Checks the signature with the project's public keys (JWKS), plus issuer, audience and expiry.
Only asymmetric algorithms are accepted, so "none" and HS256 tokens are refused.
Role lookup (users.role) is added with the database task.
"""

from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import AppError
from app.core.logging import logger

ALLOWED_ALGORITHMS = ["ES256", "RS256"]
# Supabase's audience for signed-in users. TODO: confirm against a real project token.
AUDIENCE = "authenticated"

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str | None


def _reject(reason: str) -> AppError:
    logger.warning("auth rejected", extra={"reason": reason})  # never log the token itself
    return AppError("AUTH_REQUIRED", "Please sign in again.", status=401)


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> CurrentUser:
    if credentials is None:
        raise _reject("missing bearer token")
    token = credentials.credentials
    jwks: jwt.PyJWKClient = request.app.state.jwks_client
    try:
        key = jwks.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=ALLOWED_ALGORITHMS,
            audience=AUDIENCE,
            issuer=request.app.state.settings.supabase_jwt_issuer,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.PyJWKClientConnectionError as exc:
        logger.error("jwks unreachable", extra={"reason": type(exc).__name__})
        raise AppError(
            "SERVICE_UNAVAILABLE", "Sign-in is temporarily unavailable.", status=503
        ) from exc
    except jwt.PyJWTError as exc:
        raise _reject(type(exc).__name__) from exc
    return CurrentUser(id=claims["sub"], email=claims.get("email"))
