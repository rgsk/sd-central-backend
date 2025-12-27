from fastapi import FastAPI
from routers import items
from sqlmodel import SQLModel
from db import engine

app = FastAPI()


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.get("/")
def read_root():
    return {"Hello": "World"}


app.include_router(items.router)
