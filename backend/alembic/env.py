"""
alembic/env.py
==============
Async Alembic environment for PromptScope.

Uses the asyncpg engine from app.database and imports all ORM models so that
``Base.metadata`` is fully populated before autogenerate inspects it.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Alembic Config object — access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import the application settings so we can override the DB URL at runtime
# (respects the .env file loaded by pydantic-settings).
# ---------------------------------------------------------------------------
from app.config import get_settings  # noqa: E402

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# ---------------------------------------------------------------------------
# Import *all* models so Base.metadata is populated for autogenerate.
# ---------------------------------------------------------------------------
import app.models  # noqa: F401, E402 — side-effect import populates metadata

from app.database import Base  # noqa: E402

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Offline migrations (run without a live DB connection)
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Generate SQL scripts without connecting to the database.

    Useful for reviewing migrations before applying them.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (async path)
# ---------------------------------------------------------------------------


def do_run_migrations(connection: Connection) -> None:
    """Synchronous callback executed inside ``run_sync`` to perform migrations."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations inside ``run_sync``."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations: run the async function via asyncio."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
