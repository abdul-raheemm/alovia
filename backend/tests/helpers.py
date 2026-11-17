"""Settings for tests: never read backend/.env, never touch a real database by accident."""

from typing import Any

import psycopg
from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings

UNREACHABLE_DB = "postgresql://alovia:unused@127.0.0.1:1/alovia"  # refused at once


def make_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "supabase_jwks_url": "https://example.test/auth/v1/.well-known/jwks.json",
        "supabase_jwt_issuer": "https://example.test/auth/v1",
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
