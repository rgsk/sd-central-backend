from sqlmodel import SQLModel, create_engine, Session

# SQLite file DB in project root
DATABASE_URL = "sqlite:///./database.db"

# echo=True can be helpful during development
engine = create_engine(DATABASE_URL, echo=False, connect_args={
                       "check_same_thread": False})


def get_session():
    with Session(engine) as session:
        yield session
