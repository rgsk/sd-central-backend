from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel

from admin import setup_admin
from db import DB_NAMESPACE_HEADER, engine, normalize_db_namespace
from lib.auth import get_bearer_token, get_decoded_token, require_user
from lib.env import AppEnv, env
from models import (academic_class, academic_class_subject,
                    academic_class_subject_term, academic_session,
                    academic_term, app_settings, date_sheet,
                    date_sheet_subject, enrollment, report_card,
                    report_card_subject, student, subject, user)
from models.user import UserRead
from routers import (academic_class_subject_terms, academic_class_subjects,
                     academic_classes, academic_sessions, academic_terms)
from routers import app_settings as settings
from routers import (aws, date_sheet_subjects, date_sheets, dev, enrollments,
                     public, report_card_subjects, report_cards, students,
                     subjects, test, users)


def create_all_models_without_migrations(allowed: bool):
    if env.APP_ENV is AppEnv.DEVELOPMENT and \
            'localhost' in env.DATABASE_URL and allowed:
        # listing them here is important for create_all to run for all
        all_models = [
            academic_class,
            academic_class_subject,
            academic_class_subject_term,
            academic_session,
            academic_term,
            app_settings,
            date_sheet,
            date_sheet_subject,
            enrollment,
            report_card,
            report_card_subject,
            student,
            subject,
            user,
        ]
        # below line creates all the models without running migrations
        SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic

    create_all_models_without_migrations(allowed=False)

    yield
    # Shutdown logic (optional)


app = FastAPI(lifespan=lifespan)
protected_router = APIRouter(dependencies=[Depends(require_user)])


@app.middleware("http")
async def set_db_namespace(request: Request, call_next):
    namespace_header = request.headers.get(DB_NAMESPACE_HEADER)
    if namespace_header:
        try:
            request.state.db_namespace = normalize_db_namespace(
                namespace_header
            )
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid test namespace."},
            )
    return await call_next(request)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    namespace_header = {
        "name": "X-Test-Namespace",
        "in": "header",
        "required": False,
        "schema": {"type": "string"},
        "description": "Optional test schema namespace for DB routing.",
    }
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            parameters = operation.get("parameters", [])
            if not any(
                p.get("in") == "header"
                and p.get("name") == namespace_header["name"]
                for p in parameters
            ):
                operation["parameters"] = parameters + [namespace_header]
    openapi_schema.setdefault("components", {}).setdefault(
        "securitySchemes", {}
    )["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

if env.APP_ENV is AppEnv.DEVELOPMENT:
    setup_admin(app)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/decode-token")
def decode_token(authorization: str | None = Header(default=None)):
    token = get_bearer_token(authorization)
    decoded_token = get_decoded_token(token)
    return decoded_token


@protected_router.get("/current-user", response_model=UserRead)
def get_current_user(
    request: Request,
):
    return request.state.current_user


if env.APP_ENV is AppEnv.DEVELOPMENT:
    app.include_router(dev.router)

app.include_router(test.router)
app.include_router(public.router)

protected_router.include_router(students.router)
protected_router.include_router(enrollments.router)
protected_router.include_router(academic_classes.router)
protected_router.include_router(academic_sessions.router)
protected_router.include_router(academic_terms.router)
protected_router.include_router(date_sheets.router)
protected_router.include_router(date_sheet_subjects.router)
protected_router.include_router(settings.router)
protected_router.include_router(aws.router)
protected_router.include_router(subjects.router)
protected_router.include_router(academic_class_subjects.router)
protected_router.include_router(academic_class_subject_terms.router)
protected_router.include_router(report_cards.router)
protected_router.include_router(report_card_subjects.router)
protected_router.include_router(users.router)

app.include_router(protected_router)
