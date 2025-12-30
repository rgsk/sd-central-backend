from sqlmodel import Session, create_engine

from lib.env import env

engine = create_engine(env.DATABASE_URL, echo=False)


def get_session():
    with Session(engine) as session:
        yield session
