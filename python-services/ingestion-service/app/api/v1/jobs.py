"""Ingestion job management endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.sources import get_tenant_id
from app.core.database import get_db
from app.schemas.ingestion import IngestionJobCreate, IngestionJobResponse, PaginatedResponse
from app.services.ingestion_service import IngestionService

router = APIRouter()


@router.post("/", response_model=IngestionJobResponse, status_code=202)
async def trigger_ingestion(
    payload: IngestionJobCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Trigger an ingestion job for a registered data source."""
    service = IngestionService(db)
    try:
        job = await service.run_ingestion(
            source_id=payload.source_id,
            tenant_id=tenant_id,
            options=payload.options,
        )
        return job
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/", response_model=PaginatedResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """List all ingestion jobs for the tenant with proper pagination."""
    service = IngestionService(db)
    jobs, total = await service.get_jobs(tenant_id, page, page_size)
    return PaginatedResponse(
        items=[IngestionJobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total else 0,
    )


@router.get("/{job_id}", response_model=IngestionJobResponse)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get details of a specific ingestion job."""
    service = IngestionService(db)
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
