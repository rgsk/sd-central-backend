# db.py (or wherever you create the engine)

import logging
import os
import re

from fastapi import Request
from sqlalchemy import text
from sqlmodel import Session, create_engine

from lib.env import env

# 1. Configure logging to file
sql_logger = logging.getLogger("sqlalchemy.engine")
sql_logger.setLevel(logging.INFO)  # log SQL statements

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


def apply_db_namespace(session: Session, namespace: str | None) -> None:
    if not namespace:
        return
    connection = session.connection()
    connection.execute(text(f'SET search_path TO "{namespace}", public'))


def get_session(request: Request):
    with Session(engine) as session:
        namespace = getattr(request.state, "db_namespace", None)
        if not namespace:
            namespace = os.getenv("DB_NAMESPACE")
        apply_db_namespace(session, normalize_db_namespace(namespace))
        yield session
