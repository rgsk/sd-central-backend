from fastapi import FastAPI
from routers import items

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


app.include_router(items.router)
