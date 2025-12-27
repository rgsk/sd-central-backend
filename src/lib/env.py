from dotenv import load_dotenv
import os

load_dotenv()


class _Env:
    def __init__(self):
        self.DATABASE_URL = self._get_var("DATABASE_URL")

    def _get_var(self, s: str):
        value = os.getenv(s)
        if not value:
            raise RuntimeError(
                f"{s} not set. Create a .env file from .env.example or set the env var."
            )
        return value


env = _Env()
