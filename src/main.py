from fastapi import FastAPI
from routers import items, students
from sqlmodel import SQLModel
from db import engine
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    SQLModel.metadata.create_all(engine)
    yield
    # Shutdown logic (optional)


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


app.include_router(items.router)
app.include_router(students.router)
