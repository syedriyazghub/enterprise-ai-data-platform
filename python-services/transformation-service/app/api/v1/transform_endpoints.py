"""Transformation API endpoints."""
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.transformation_service import TransformationService

router = APIRouter()


class TransformationRuleSchema(BaseModel):
    transformation_type: str
    source_field: str
    target_field: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class TransformRequest(BaseModel):
    records: list[dict[str, Any]] = Field(..., min_length=1)
    rules: list[TransformationRuleSchema] = Field(..., min_length=1)
    tenant_id: str = "default"


@router.post("/transform")
async def transform_data(request: TransformRequest):
    """Apply transformation rules to a dataset."""
    service = TransformationService()
    try:
        job, transformed_records = service.transform(
            records=request.records,
            rules=[r.model_dump() for r in request.rules],
            tenant_id=request.tenant_id,
        )
        return {
            "job_id": job.job_id,
            "status": job.status,
            "records": transformed_records,
            "rules_applied": job.rules_applied,
            "records_in": job.records_in,
            "records_out": job.records_out,
            "errors": job.errors,
            "duration_ms": job.duration_ms,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/transformations")
async def list_transformations():
    """List all available transformation types with descriptions."""
    service = TransformationService()
    types = service.list_transformation_types()
    return {"transformations": types, "total": len(types)}
