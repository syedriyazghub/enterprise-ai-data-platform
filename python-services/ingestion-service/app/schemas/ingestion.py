"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.models.pg_models import SourceType, JobStatus


class DataSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_type: SourceType
    connection_config: dict[str, Any] = Field(default_factory=dict)

    @field_validator("connection_config")
    @classmethod
    def validate_config_not_empty(cls, v, info):
        return v


class DataSourceResponse(BaseModel):
    id: UUID
    tenant_id: str
    name: str
    source_type: SourceType
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestionJobCreate(BaseModel):
    source_id: UUID
    options: dict[str, Any] = Field(default_factory=dict)


class IngestionJobResponse(BaseModel):
    id: UUID
    source_id: UUID
    tenant_id: str
    status: JobStatus
    records_ingested: int
    records_failed: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FileUploadResponse(BaseModel):
    job_id: str
    file_name: str
    file_size_bytes: int
    source_type: str
    status: str
    message: str


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int
