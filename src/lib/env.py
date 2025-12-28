from dotenv import load_dotenv
import os

load_dotenv()


class _Env:
    def __init__(self):
        self.DATABASE_URL = self._get_var("DATABASE_URL")
        self.AWS_ACCESS_KEY = self._get_var('AWS_ACCESS_KEY')
        self.AWS_SECRET_ACCESS_KEY = self._get_var('AWS_SECRET_ACCESS_KEY')
        self.AWS_REGION = self._get_var('AWS_REGION', "us-east-1")
        self.AWS_PUBLIC_BUCKET = self._get_var(
            'AWS_PUBLIC_BUCKET', "public-ai-exp"
        )
        self.AWS_PRIVATE_BUCKET = self._get_var(
            'AWS_PRIVATE_BUCKET', "private-ai-exp"
        )

    def _get_var(self, s: str, default: str | None = None):
        value = os.getenv(s, default)
        if not value:
            raise RuntimeError(
                f"{s} not set. Create a .env file from .env.example or set the env var."
            )
        return value


env = _Env()
