"""Domain models for ingestion service (SQLAlchemy)."""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, Integer, JSON, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class SourceType(str, Enum):
    REST_API = "rest_api"
    SOAP_API = "soap_api"
    GRAPHQL = "graphql"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    XML = "xml"
    JSON = "json"
    PARQUET = "parquet"
    AVRO = "avro"
    ORC = "orc"
    GOOGLE_SHEETS = "google_sheets"
    AWS_S3 = "aws_s3"
    AZURE_BLOB = "azure_blob"
    FTP = "ftp"
    SFTP = "sftp"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQL_SERVER = "sql_server"
    ORACLE = "oracle"
    MONGODB = "mongodb"
    REDIS = "redis"
    KAFKA = "kafka"
    RABBITMQ = "rabbitmq"
    AZURE_SERVICE_BUS = "azure_service_bus"
    AMAZON_SQS = "amazon_sqs"
    GOOGLE_PUBSUB = "google_pubsub"
    WEBHOOK = "webhook"
    EMAIL = "email"
    MANUAL_UPLOAD = "manual_upload"
    FHIR_API = "fhir_api"
    HL7 = "hl7"
    EDI = "edi"
    IOT_STREAM = "iot_stream"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class DataSourceConfig(Base):
    """Registered data source configuration."""
    __tablename__ = "data_source_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType), nullable=False)
    connection_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(String(100))

    jobs: Mapped[list["IngestionJobRecord"]] = relationship("IngestionJobRecord", back_populates="source")


class IngestionJobRecord(Base):
    """Tracks each ingestion job execution."""
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("data_source_configs.id"))
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.PENDING)
    records_ingested: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source: Mapped["DataSourceConfig"] = relationship("DataSourceConfig", back_populates="jobs")
