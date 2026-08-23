"""Alembic environment for Margin's SQLAlchemy metadata."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from margin_api import (
    models,  # noqa: F401  # Import models to register metadata for autogeneration.
)
from margin_api.config import Settings
from margin_api.database import Base, create_database_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    """Use the API setting unless Alembic receives an explicit URL override.

    Tests supply ``sqlalchemy.url`` directly on their Alembic ``Config``. Normal
    invocations intentionally use ``Settings`` so the API and migration command
    read the same ``apps/api/.env`` database setting.
    """

    configured_url = config.get_main_option("sqlalchemy.url")
    return configured_url or Settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_database_engine(get_database_url(), echo=False)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
