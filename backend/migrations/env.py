"""Alembic environment. Uses DATABASE_URL from backend/.env unless a caller (the migration
tests) passes another URL in config.attributes["database_url"]."""

from alembic import context
from sqlalchemy import make_url

import app.modules.predictions.models
import app.modules.users.models  # noqa: F401  (registers the tables on Base.metadata)
from app.core.database import Base, make_engine

config = context.config
target_metadata = Base.metadata


def _database_url() -> str:
    url = config.attributes.get("database_url")
    if url:
        return str(url)
    from app.core.config import get_settings

    return get_settings().database_url


def run_offline() -> None:
    """`alembic upgrade head --sql`: print the SQL instead of running it."""
    url = make_url(_database_url()).set(drivername="postgresql+psycopg")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_online() -> None:
    engine = make_engine(_database_url())
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()  # close pooled connections; nothing else reuses this engine


if context.is_offline_mode():
    run_offline()
else:
    run_online()
