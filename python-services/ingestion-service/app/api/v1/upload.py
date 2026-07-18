"""File upload endpoints supporting CSV, Excel, JSON, XML, PDF, ZIP."""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.pg_models import SourceType
from app.schemas.ingestion import FileUploadResponse
from app.services.ingestion_service import IngestionService

router = APIRouter()

EXTENSION_TO_SOURCE_TYPE = {
    ".csv": SourceType.CSV,
    ".xlsx": SourceType.EXCEL,
    ".xls": SourceType.EXCEL,
    ".json": SourceType.JSON,
    ".xml": SourceType.XML,
    ".parquet": SourceType.PARQUET,
    ".pdf": SourceType.PDF,
}


@router.post("/", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a file for ingestion.
    Supports: CSV, Excel, JSON, XML, Parquet, PDF.
    Max size: 500MB.
    """
    # Validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Detect source type from extension
    _, ext = os.path.splitext(file.filename.lower())
    source_type = EXTENSION_TO_SOURCE_TYPE.get(ext)
    if not source_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {list(EXTENSION_TO_SOURCE_TYPE.keys())}",
        )

    service = IngestionService(db)
    result = await service.ingest_file(
        tenant_id="default-tenant",
        file_content=content,
        file_name=file.filename,
        source_type=source_type,
    )

    return FileUploadResponse(
        job_id=result["job_id"],
        file_name=result["file_name"],
        file_size_bytes=result["file_size_bytes"],
        source_type=result["source_type"],
        status=result["status"],
        message=f"Successfully ingested {result.get('records_ingested', 0)} records",
    )
