import os
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

class AppEnv(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class _Env:
    def __init__(self):
        self.APP_ENV = self._get_app_env()
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

    def _get_app_env(self):
        value = self._get_var("APP_ENV")
        try:
            return AppEnv(value)
        except ValueError:
            allowed_list = ", ".join(sorted(e.value for e in AppEnv))
            raise RuntimeError(
                f"APP_ENV must be one of: {allowed_list}. Got: {value}"
            )


env = _Env()
