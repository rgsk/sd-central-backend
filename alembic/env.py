import os
import re
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Ensure app modules are importable when running Alembic.
PROJECT_SRC = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "src"))
if PROJECT_SRC not in sys.path:
    sys.path.append(PROJECT_SRC)

from sqlmodel import SQLModel  # noqa: E402

from lib.env import env  # noqa: E402
from models import (academic_class, academic_class_subject,  # noqa: F401, E402
                    academic_class_subject_term, academic_session,
                    academic_term, app_settings, date_sheet,
                    date_sheet_subject, enrollment, report_card,
                    report_card_subject, student, subject, user)

_ = [academic_class, academic_class_subject,
     academic_class_subject_term, academic_session, academic_term,
     app_settings, date_sheet, date_sheet_subject, enrollment, report_card,
     report_card_subject, student, subject, user]

# Use SQLModel metadata for autogenerate support.
target_metadata = SQLModel.metadata

config.set_main_option("sqlalchemy.url", env.DATABASE_URL)

_NAMESPACE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _normalize_db_namespace(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if not _NAMESPACE_RE.fullmatch(value):
        raise RuntimeError("Invalid DB_NAMESPACE")
    return value

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    namespace = _normalize_db_namespace(os.getenv("DB_NAMESPACE"))

    with connectable.connect() as connection:
        configure_kwargs = {
            "connection": connection,
            "target_metadata": target_metadata,
        }
        if namespace:
            configure_kwargs["version_table_schema"] = namespace

        context.configure(**configure_kwargs)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
