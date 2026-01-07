from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import auth
from sqlmodel import SQLModel

from admin import setup_admin
from db import engine
from lib.env import AppEnv, env
from lib.firebase_admin import get_firebase_app
from models import (academic_class, academic_class_subject, academic_session,
                    academic_term, app_settings, enrollment, item, report_card,
                    report_card_subject, student, subject)
from routers import (academic_class_subjects, academic_classes,
                     academic_sessions, academic_terms)
from routers import app_settings as settings
from routers import (aws, enrollments, items, report_card_subjects,
                     report_cards, students, subjects, test)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # listing them here is important for create_all to run for all
    all_models = [
        academic_class,
        academic_class_subject,
        academic_session,
        academic_term,
        app_settings,
        enrollment,
        item,
        report_card,
        report_card_subject,
        student,
        subject,
    ]
    SQLModel.metadata.create_all(engine)
    yield
    # Shutdown logic (optional)


app = FastAPI(lifespan=lifespan)

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
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    id_token = authorization.removeprefix("Bearer ").strip()
    if not id_token:
        raise HTTPException(status_code=401, detail="Missing token")
    get_firebase_app()
    decoded = auth.verify_id_token(id_token)
    return decoded


if env.APP_ENV is AppEnv.DEVELOPMENT:
    app.include_router(test.router)

app.include_router(items.router)
app.include_router(students.router)
app.include_router(enrollments.router)
app.include_router(academic_classes.router)
app.include_router(academic_sessions.router)
app.include_router(academic_terms.router)
app.include_router(settings.router)
app.include_router(aws.router)
app.include_router(subjects.router)
app.include_router(academic_class_subjects.router)
app.include_router(report_cards.router)
app.include_router(report_card_subjects.router)
