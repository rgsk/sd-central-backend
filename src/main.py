from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from db import engine
from models import (academic_class, academic_class_subject, academic_session,
                    academic_term, item, report_card, report_card_subject,
                    student, subject)
from routers import (academic_class_subjects, academic_classes,
                     academic_sessions, academic_terms, aws, items,
                     report_card_subjects, report_cards, students, subjects,
                     test)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # listing them here is important for create_all to run for all
    all_models = [
        academic_class,
        academic_class_subject,
        academic_session,
        academic_term,
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


@app.get("/")
def read_root():
    return {"Hello": "World"}


app.include_router(test.router)
app.include_router(items.router)
app.include_router(students.router)
app.include_router(academic_classes.router)
app.include_router(academic_sessions.router)
app.include_router(academic_terms.router)
app.include_router(aws.router)
app.include_router(subjects.router)
app.include_router(academic_class_subjects.router)
app.include_router(report_cards.router)
app.include_router(report_card_subjects.router)
