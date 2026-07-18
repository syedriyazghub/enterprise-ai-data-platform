"""Pydantic settings for AI service."""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8004
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8100

    REDIS_URL: str = "redis://localhost:6379/0"

    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.1


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
