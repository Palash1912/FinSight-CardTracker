"""Alembic environment configuration.

Reads DATABASE_URL_SYNC from the environment so that the async URL used by
the application is never passed to Alembic (which requires a synchronous driver).
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.models.base import Base

# Alembic Config object — provides access to alembic.ini values
config = context.config

# Set up Python logging from the config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData for 'autogenerate' support
target_metadata = Base.metadata

# Override sqlalchemy.url with env var when available
database_url = os.environ.get("DATABASE_URL_SYNC")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an engine and connects to the database to run migrations.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
