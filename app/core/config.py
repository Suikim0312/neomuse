"""Application configuration loaded from environment variables.

All settings are centralized here so that switching from SQLite to
PostgreSQL (or any other backend) only requires changing environment
variables, not code.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Security / JWT
    SECRET_KEY: str = "change_me_super_secret_key_for_jwt_signing"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Misc
    DEBUG: bool = True
    PROJECT_NAME: str = "NeoMuse – Smart Museum Management System"
    REPORTS_DIR: str = "app/reports"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
