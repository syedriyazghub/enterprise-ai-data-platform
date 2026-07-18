"""Pydantic settings for scheduling service."""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8006
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    REDIS_URL: str = "redis://localhost:6379/0"

    INGESTION_SERVICE_URL: str = "http://localhost:8001"
    VALIDATION_SERVICE_URL: str = "http://localhost:8002"
    TRANSFORMATION_SERVICE_URL: str = "http://localhost:8003"
    AI_SERVICE_URL: str = "http://localhost:8004"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
