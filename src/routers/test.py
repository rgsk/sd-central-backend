import os
import re
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import Session

from db import get_session
from lib.env import env

router = APIRouter(prefix="/test", tags=["test"])

_NAMESPACE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_BLOCKED_NAMESPACES = {"public", "pg_catalog", "information_schema"}

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMAND_ERROR_MESSAGE = "Command failed."


class CommandResult(BaseModel):
    status: str
    command: str
    output: str


class NamespaceList(BaseModel):
    namespaces: list[str]


def _run_command(
    command: list[str], namespace: str | None = None
) -> CommandResult:
    command_env = os.environ.copy()
    if "localhost" not in env.DATABASE_URL and not namespace:
        raise HTTPException(
            status_code=400,
            detail="DB namespace required for non-local database.",
        )
    if namespace:
        normalized = namespace.strip()
        if (
            not normalized
            or not _NAMESPACE_RE.fullmatch(normalized)
            or normalized in _BLOCKED_NAMESPACES
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid DB namespace.",
            )
        command_env["DB_NAMESPACE"] = normalized
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=command_env,
    )
    combined_output = f"{result.stdout}{result.stderr}"
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": COMMAND_ERROR_MESSAGE,
                "command": " ".join(command),
                "output": combined_output,
            },
        )
    return CommandResult(
        status="ok",
        command=" ".join(command),
        output=combined_output,
    )


@router.get("/namespaces", response_model=NamespaceList)
def list_namespaces(session: Session = Depends(get_session)):
    rows = session.connection().execute(
        text(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name NOT IN ('information_schema') "
            "AND schema_name NOT LIKE 'pg_%' "
            "ORDER BY schema_name"
        )
    )
    return NamespaceList(namespaces=[row[0] for row in rows])


@router.post("/reset_db", response_model=CommandResult)
def reset_db(request: Request):
    namespace = getattr(request.state, "db_namespace", None)
    result = _run_command(["make", "reset_db"], namespace)
    return result


@router.post("/migrate_db", response_model=CommandResult)
def migrate_db(request: Request):
    namespace = getattr(request.state, "db_namespace", None)
    return _run_command(["make", "migrate_db"], namespace)


@router.post("/seed_db", response_model=CommandResult)
def seed_db(request: Request, folder: str = Query(..., min_length=1)):
    namespace = getattr(request.state, "db_namespace", None)
    return _run_command(["make", "seed_db", folder], namespace)


@router.post("/refresh_db", response_model=CommandResult)
def refresh_db(request: Request, folder: str = Query(..., min_length=1)):
    namespace = getattr(request.state, "db_namespace", None)
    return _run_command(["make", "refresh_db", folder], namespace)


@router.post("/verify_seed", response_model=CommandResult)
def verify_seed(
    request: Request,
    folder: str = Query(..., min_length=1),
    logical_compare: bool = Query(False),
):
    command = ["make", "verify_seed"]
    if logical_compare:
        command.append("LOGICAL_COMPARE=1")
    command.append(folder)
    namespace = getattr(request.state, "db_namespace", None)
    return _run_command(command, namespace)


@router.post("/populate_seed", response_model=CommandResult)
def populate_seed(
    request: Request,
    folder: str = Query(..., min_length=1),
):
    namespace = getattr(request.state, "db_namespace", None)
    return _run_command(["make", "populate_seed", folder], namespace)


@router.post("/firebase_custom_token", response_model=CommandResult)
def firebase_custom_token(request: Request, email: str = Query(..., min_length=1)):
    namespace = getattr(request.state, "db_namespace", None)
    return _run_command(
        ["python", "scripts/create_firebase_custom_token.py", email],
        namespace
    )
