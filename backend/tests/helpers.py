"""Shared test helpers: settings that never read backend/.env, fast test engines, and
locally signed tokens (no Supabase call)."""

import time
import uuid
from typing import Any

import jwt
import psycopg
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import FastAPI
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.pool import StaticPool

from app.core.config import CONSENT_VERSION, Settings
from app.main import create_app

UNREACHABLE_DB = "postgresql://alovia:unused@127.0.0.1:1/alovia"  # refused at once
ISSUER = "https://example.test/auth/v1"
KID = "test-key"
KEY = ec.generate_private_key(ec.SECP256R1())
OTHER_KEY = ec.generate_private_key(ec.SECP256R1())


def make_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "supabase_jwks_url": "https://example.test/auth/v1/.well-known/jwks.json",
        "supabase_jwt_issuer": ISSUER,
        "database_url": UNREACHABLE_DB,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def working_engine() -> Engine:
    """In-memory database that answers SELECT 1, so /health tests stay fast and offline."""
    return create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )


def down_engine() -> Engine:
    """Engine whose every connection attempt fails at once, like an unreachable database."""

    def refuse() -> Any:
        raise psycopg.OperationalError("connection refused (test)")

    return create_engine("postgresql+psycopg://", creator=refuse)


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


def bearer(**overrides: Any) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(**overrides)}"}


def make_app(**settings: Any) -> FastAPI:
    """App that accepts tokens signed with KEY."""
    app = create_app(make_settings(**settings))
    app.state.jwks_client = FakeJWKClient(jwks_for(KEY))
    return app


def add_linked_patient(
    engine: Engine, *, consent: bool = True, role: str = "patient", link: bool = True
) -> tuple[uuid.UUID, uuid.UUID]:
    """A signed-up test patient: users row, linked patients row and (by default) the current
    consent. Returns (user_id, patient_id)."""
    user_id = uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO users (id, email, role) VALUES (:id, :e, :r)"),
            {"id": user_id, "e": f"{user_id}@example.test", "r": role},
        )
        patient_id: uuid.UUID = conn.execute(
            text("INSERT INTO patients (user_id, name) VALUES (:u, 'Test Patient 3') RETURNING id"),
            {"u": user_id if link else None},
        ).scalar_one()
        if consent:
            conn.execute(
                text(
                    "INSERT INTO consents (user_id, consent_version, age_confirmed_18_plus, "
                    "accepted_at) VALUES (:u, :v, true, now())"
                ),
                {"u": user_id, "v": CONSENT_VERSION},
            )
    return user_id, patient_id


def add_account(engine: Engine, role: str, *, consent: bool = True) -> uuid.UUID:
    """A users row (doctor or admin) with the current consent by default. Returns user_id."""
    user_id = uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO users (id, email, role) VALUES (:id, :e, :r)"),
            {"id": user_id, "e": f"{user_id}@example.test", "r": role},
        )
        if consent:
            conn.execute(
                text(
                    "INSERT INTO consents (user_id, consent_version, age_confirmed_18_plus, "
                    "accepted_at) VALUES (:u, :v, true, now())"
                ),
                {"u": user_id, "v": CONSENT_VERSION},
            )
    return user_id


def add_doctor(
    engine: Engine, *, consent: bool = True, active: bool = True
) -> tuple[uuid.UUID, uuid.UUID]:
    """A test doctor account. Returns (user_id, doctor_id)."""
    user_id = add_account(engine, "doctor", consent=consent)
    with engine.begin() as conn:
        doctor_id: uuid.UUID = conn.execute(
            text(
                "INSERT INTO doctors (user_id, name, is_active) "
                "VALUES (:u, 'Test Doctor', :a) RETURNING id"
            ),
            {"u": user_id, "a": active},
        ).scalar_one()
    return user_id, doctor_id


def assign(
    engine: Engine,
    doctor_id: uuid.UUID,
    patient_id: uuid.UUID,
    *,
    primary: bool = False,
    removed: bool = False,
) -> None:
    """Assign a doctor to a patient (assigned_by = a fresh admin)."""
    admin = add_account(engine, "admin")
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO doctor_patient_assignments (doctor_id, patient_id, is_primary, "
                "assigned_by, assigned_at, removed_at) VALUES (:d, :p, :pr, :by, now(), "
                "CASE WHEN :rm THEN now() END)"
            ),
            {"d": doctor_id, "p": patient_id, "pr": primary, "by": admin, "rm": removed},
        )
