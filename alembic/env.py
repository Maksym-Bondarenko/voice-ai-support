"""Alembic environment for Delivery-AI project."""

from __future__ import with_statement

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ───────────────────────────────────────── sys.path
# Make sure "app" is importable when you run "alembic" from project root.
BASE_DIR = os.path.abspath(os.path.join(os.getcwd()))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# ───────────────────────────────────────── models & metadata
from app.db.base import Base            # declarative_base()
import app.db.models  # noqa: F401      # registers tables

target_metadata = Base.metadata         # <- THIS is what Alembic needs

# ───────────────────────────────────────── Alembic config
config = context.config                 # already loaded alembic.ini

# If you prefer to pull DATABASE_URL from the same .env:
if not config.get_main_option("sqlalchemy.url"):
    from app.core.config import get_settings
    config.set_main_option("sqlalchemy.url", get_settings().DATABASE_URL)

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations without DB connection (generates SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,   # <-- pass it here
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with an Engine connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,   # <-- …and here
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()