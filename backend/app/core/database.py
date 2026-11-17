"""Database engine and model base (DATABASE.md). Only the backend connects (DEC-001)."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import Engine, MetaData, create_engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session

# fixed constraint names, so migrations are predictable and reviewable
NAMING = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


def make_engine(url: str) -> Engine:
    # Supabase gives "postgresql://..."; use the installed psycopg 3 driver
    return create_engine(
        make_url(url).set(drivername="postgresql+psycopg"),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},  # /health must not hang on a dead database
    )


def get_db(request: Request) -> Iterator[Session]:
    """One session per request. Services commit explicitly; anything not committed is rolled
    back when the session closes, so a failed request changes nothing (ERROR_HANDLING.md §6)."""
    with Session(request.app.state.engine, expire_on_commit=False) as session:
        yield session
