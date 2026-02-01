# db.py (or wherever you create the engine)

import logging
import os
import re

from fastapi import HTTPException, Request
from sqlalchemy import event, text
from sqlalchemy.orm import Session as SASession
from sqlmodel import Session, create_engine

from lib.env import AppEnv, env

# 1. Configure logging to file
sql_logger = logging.getLogger("sqlalchemy.engine")
sql_logger.setLevel(logging.INFO)  # log SQL statements

if env.APP_ENV == AppEnv.DEVELOPMENT:
    if os.path.exists("sql.log"):
        os.remove("sql.log")
    open("sql.log", "w").close()

    file_handler = logging.FileHandler("sql.log")
    file_handler.setLevel(logging.INFO)

    # Optional: cleaner formatting
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    sql_logger.addHandler(file_handler)

# 2. SQLModel engine
# echo=False to avoid console spam
engine = create_engine(env.DATABASE_URL, echo=False)

# 3. Dependency


DB_NAMESPACE_HEADER = "x-test-namespace"
_NAMESPACE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def normalize_db_namespace(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if not _NAMESPACE_RE.fullmatch(value):
        raise ValueError("Invalid namespace")
    return value


def apply_db_namespace_to_connection(
    connection, namespace: str | None
) -> None:
    if not namespace:
        return
    exists = connection.execute(
        text(
            "SELECT 1 FROM information_schema.schemata "
            "WHERE schema_name = :schema_name"
        ),
        {"schema_name": namespace},
    ).first()
    if not exists:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown DB namespace: {namespace}",
        )
    connection.execute(text(f'SET search_path TO "{namespace}", public'))


def get_session(request: Request):
    with Session(engine) as session:
        namespace = getattr(request.state, "db_namespace", None)
        if not namespace:
            namespace = os.getenv("DB_NAMESPACE")
        session.info["db_namespace"] = normalize_db_namespace(namespace)
        yield session


@event.listens_for(SASession, "after_begin")
def _apply_namespace_after_begin(
    session: SASession,
    transaction,
    connection,
) -> None:
    namespace = session.info.get("db_namespace")
    if not namespace:
        return
    apply_db_namespace_to_connection(connection, namespace)
