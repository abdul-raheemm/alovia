"""Database engine and model base (DATABASE.md). Only the backend connects (DEC-001)."""

from sqlalchemy import Engine, MetaData, create_engine, make_url
from sqlalchemy.orm import DeclarativeBase

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
