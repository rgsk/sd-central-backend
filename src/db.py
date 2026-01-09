# db.py (or wherever you create the engine)

import logging

from sqlmodel import Session, create_engine

from lib.env import env

# 1. Configure logging to file
sql_logger = logging.getLogger("sqlalchemy.engine")
sql_logger.setLevel(logging.INFO)  # log SQL statements

file_handler = logging.FileHandler("sql.log")
file_handler.setLevel(logging.INFO)

# Optional: cleaner formatting
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)

sql_logger.addHandler(file_handler)

# 2. SQLModel engine
# echo=False to avoid console spam
engine = create_engine(env.DATABASE_URL, echo=False)

# 3. Dependency


def get_session():
    with Session(engine) as session:
        yield session
