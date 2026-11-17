"""Database engine and model base (DATABASE.md). Only the backend connects (DEC-001)."""

import uuid
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy import DateTime, Engine, ForeignKey, MetaData, create_engine, func, make_url
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

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


# Column helpers shared by every module (DATABASE.md §2 conventions)
def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )


def created_now() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


def fk(target: str, **kwargs: Any) -> Any:
    """Foreign key with ON DELETE RESTRICT (DATABASE.md §2)."""
    return mapped_column(ForeignKey(target, ondelete="RESTRICT"), **kwargs)


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
