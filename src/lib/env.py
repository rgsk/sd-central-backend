from dotenv import load_dotenv
import os

load_dotenv()


def get_var(s: str):
    value = os.getenv(s)
    if not value:
        raise RuntimeError(
            f"{s} not set. Create a .env file from .env.example or set the env var."
        )
    return value


DATABASE_URL = get_var("DATABASE_URL")
