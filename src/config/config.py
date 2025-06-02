from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets

from typing import Set
from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from functools import lru_cache
from pytz import timezone, BaseTzInfo


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    SERVER_NAME: str = "Gym Backend"
    SERVER_HOST: str = "http://localhost:8000"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "mahdi@1380"
    POSTGRES_DB: str = "gym_backend"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    DB_POOL_SIZE: int = 5  # Default number of connections to keep open
    DB_MAX_OVERFLOW: int = 10  # Maximum number of connections above pool_size
    DB_POOL_TIMEOUT: int = (
        30  # Seconds to wait before giving up on getting a connection
    )
    DB_POOL_RECYCLE: int = 1800  # Recycle connections after 30 minutes

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Authorization
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # CORS settings
    CORS_ALLOW_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: str = "true"
    CORS_ALLOW_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS,PATCH"
    CORS_ALLOW_HEADERS: str = (
        "Accept,Authorization,Content-Type,X-CSRF-Token,X-Requested-With"
    )

    # CSRF settings
    CSRF_TOKEN_SECRET: str
    CSRF_COOKIE_DOMAIN: str = "localhost"
    CSRF_COOKIE_SAMESITE: str = "Lax"
    CSRF_COOKIE_SECURE: bool = True

    # SMTP Server
    MAIL_HOST: str
    MAIL_PORT: int
    MAIL_USER: str
    MAIL_PASSWORD: str
    MAIL_FROM_ADDRESS: str

    # File Storage
    LIARA_ENDPOINT: str
    LIARA_BUCKET_NAME: str
    LIARA_ACCESS_KEY: str
    LIARA_SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env" if os.getenv("ENVIRONMENT") != "production" else ".env.prod",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def database_url(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    @property
    def redis_url(self) -> str:
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else "@"
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache()
def get_settings():
    env_file = ".env.prod" if os.getenv("ENVIRONMENT") == "production" else ".env"
    load_dotenv(dotenv_path=env_file, override=True)
    settings = Settings()
    return settings


settings = get_settings()
