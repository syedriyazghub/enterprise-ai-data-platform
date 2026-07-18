"""Pydantic settings for PDF service."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8005
    TESSERACT_CMD: str = "/usr/bin/tesseract"
    OCR_LANGUAGE: str = "eng"
    MAX_PDF_SIZE_MB: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
