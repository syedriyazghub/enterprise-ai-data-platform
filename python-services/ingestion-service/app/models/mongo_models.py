"""MongoDB document models using Beanie ODM."""
from datetime import datetime
from typing import Any, Optional
from beanie import Document, Indexed
from pydantic import Field
import uuid


class IngestionJob(Document):
    """Stores raw ingested data and job metadata in MongoDB."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Indexed(str)
    source_id: str
    source_type: str
    raw_data: list[dict[str, Any]] = Field(default_factory=list)
    schema_detected: Optional[dict] = None
    record_count: int = 0
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "ingestion_jobs"
        indexes = ["tenant_id", "source_id", "created_at"]


class DataSource(Document):
    """Stores data source metadata and connection info."""

    source_id: Indexed(str, unique=True)
    tenant_id: Indexed(str)
    name: str
    source_type: str
    tags: list[str] = Field(default_factory=list)
    last_ingested_at: Optional[datetime] = None
    total_records_ingested: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "data_sources"
