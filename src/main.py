from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from db import engine
from models import academic_class, academic_session, item, student
from routers import academic_classes, academic_sessions, aws, items, students


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # listing them here is important for create_all to run for all
    all_models = [academic_class, academic_session, item, student]
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


app.include_router(items.router)
app.include_router(students.router)
app.include_router(academic_classes.router)
app.include_router(academic_sessions.router)
app.include_router(aws.router)
