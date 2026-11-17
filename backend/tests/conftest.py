"""Shared database fixtures. Tests that need tables use the separate alovia-test project
(TEST_DATABASE_URL, DEC-034); it is migrated once per run and emptied at the end."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, make_url

from app.core.config import get_settings
from app.core.database import make_engine

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def project_ref(url: str) -> str | None:
    """Supabase project id: from user "postgres.<ref>" (pooler) or host "db.<ref>.supabase.co"."""
    u = make_url(url)
    if (u.username or "").startswith("postgres."):
        return (u.username or "").split(".", 1)[1]
    host = u.host or ""
    if host.startswith("db.") and host.endswith(".supabase.co"):
        return host.split(".")[1]
    return None


def alembic_config(url: str) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.attributes["database_url"] = url
    return cfg


@pytest.fixture(scope="session")
def test_db_url() -> str:
    settings = get_settings()
    url = settings.test_database_url
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set in backend/.env")
    # safety: these tests drop every table, so they must never reach the main project
    test_ref = project_ref(url)
    assert test_ref, "TEST_DATABASE_URL is not a recognisable Supabase URL; refusing to run"
    assert test_ref != project_ref(settings.database_url), "TEST_DATABASE_URL is the main project"
    return url


@pytest.fixture(scope="session")
def engine(test_db_url: str) -> Iterator[Engine]:
    cfg = alembic_config(test_db_url)
    command.downgrade(cfg, "base")  # start from empty, even after an interrupted run
    command.upgrade(cfg, "head")
    eng = make_engine(test_db_url)
    yield eng
    eng.dispose()
    command.downgrade(cfg, "base")  # leave the test database empty
