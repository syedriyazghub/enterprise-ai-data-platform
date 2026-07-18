"""Pydantic settings for validation service."""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8002
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ai_platform"
    POSTGRES_USER: str = "platform_user"
    POSTGRES_PASSWORD: str = "platform_pass"
    MONGODB_URI: str = "mongodb://localhost:27017/ai_platform"
    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
