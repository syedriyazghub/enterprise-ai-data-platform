"""Pydantic settings for transformation service."""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8003
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
