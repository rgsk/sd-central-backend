from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import aws, items, students
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
app.include_router(aws.router)
