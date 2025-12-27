from sqlmodel import create_engine, Session
import os

# Use DATABASE_URL from env if set, otherwise use provided Postgres URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5498/postgres",
)


engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    with Session(engine) as session:
        yield session
