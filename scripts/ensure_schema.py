import os
import re
import sys

from sqlalchemy import create_engine, text

SCRIPT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from lib.env import env  # noqa: E402

_NAMESPACE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_BLOCKED = {"public", "pg_catalog", "information_schema"}


def _normalize_db_namespace(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if not _NAMESPACE_RE.fullmatch(value):
        raise RuntimeError("Invalid DB_NAMESPACE.")
    if value in _BLOCKED:
        raise RuntimeError(f"DB_NAMESPACE '{value}' is not allowed.")
    return value


def main() -> None:
    namespace = _normalize_db_namespace(os.getenv("DB_NAMESPACE"))
    if not namespace:
        return
    engine = create_engine(env.DATABASE_URL, echo=False)
    with engine.begin() as connection:
        connection.execute(
            text(f'CREATE SCHEMA IF NOT EXISTS "{namespace}"')
        )


if __name__ == "__main__":
    main()
