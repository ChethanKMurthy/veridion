"""Alembic environment: migrates the database configured in Veridion's settings."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from veridion import models  # noqa: F401  - register every table on the metadata
from veridion.config import get_settings
from veridion.db import Base, UTCDateTime

config = context.config

if config.config_file_name is not None and config.attributes.get("configure_logging", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _url() -> str:
    # An explicit URL (tests, `veridion db` with an override) wins over the settings.
    return config.attributes.get("database_url") or get_settings().database_url


def _render_item(type_, obj, autogen_context):
    # Migrations should not import application code: UTCDateTime is a timezone-aware
    # DateTime at the database level, so render it as one.
    if type_ == "type" and isinstance(obj, UTCDateTime):
        return "sa.DateTime(timezone=True)"
    return False


def _options(url: str) -> dict:
    return {
        "target_metadata": target_metadata,
        "compare_type": True,
        "render_item": _render_item,
        # SQLite cannot ALTER most constraints; batch mode recreates the table instead.
        "render_as_batch": url.startswith("sqlite"),
    }


def run_migrations_offline() -> None:
    url = _url()
    context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"}, **_options(url))
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _url()
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, **_options(url))
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
