"""
Data source management endpoints.

Improvements:
- Real JWT tenant extraction (replaces hardcoded placeholder)
- Schema discovery endpoint
- Preview endpoint
- Connector marketplace listing
- Consistent paginated responses
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.ingestion import DataSourceCreate, DataSourceResponse, PaginatedResponse
from app.services.ingestion_service import IngestionService
from app.connectors.registry import get_registry

router = APIRouter()


def get_tenant_id(authorization: str = Header(default="")) -> str:
    """
    Extract tenant_id from JWT Bearer token.
    Falls back to 'default-tenant' when no token is present (dev mode).
    """
    if not authorization.startswith("Bearer "):
        return "default-tenant"
    token = authorization.removeprefix("Bearer ").strip()
    try:
        import base64, json as _json
        # Decode payload segment (index 1) without verifying signature
        payload_b64 = token.split(".")[1]
        # Pad to multiple of 4
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("tenant_id") or payload.get("sub") or "default-tenant"
    except Exception:
        return "default-tenant"


@router.post("/", response_model=DataSourceResponse, status_code=201)
async def create_data_source(
    payload: DataSourceCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Register a new data source configuration."""
    service = IngestionService(db)
    source = await service.create_source(
        tenant_id=tenant_id,
        name=payload.name,
        source_type=payload.source_type,
        connection_config=payload.connection_config,
        created_by="api",
    )
    return source


@router.get("/", response_model=PaginatedResponse)
async def list_data_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """List all registered data sources for the tenant."""
    service = IngestionService(db)
    sources, total = await service.get_sources(tenant_id, page, page_size)
    return PaginatedResponse(
        items=[DataSourceResponse.model_validate(s) for s in sources],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total else 0,
    )


@router.get("/{source_id}", response_model=DataSourceResponse)
async def get_data_source(source_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single data source by ID."""
    service = IngestionService(db)
    source = await service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.delete("/{source_id}", status_code=204)
async def delete_data_source(source_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a registered data source."""
    service = IngestionService(db)
    deleted = await service.delete_source(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")


@router.post("/{source_id}/test")
async def test_connection(source_id: UUID, db: AsyncSession = Depends(get_db)):
    """Test connectivity to a registered data source."""
    service = IngestionService(db)
    try:
        result = await service.test_source_connection(source_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{source_id}/schema")
async def discover_schema(source_id: UUID, db: AsyncSession = Depends(get_db)):
    """Discover schema from a registered data source."""
    service = IngestionService(db)
    try:
        schema = await service.discover_source_schema(source_id)
        return {
            "source_id": str(source_id),
            "fields": [
                {
                    "name": f.name,
                    "data_type": f.data_type,
                    "nullable": f.nullable,
                    "sample_values": f.sample_values,
                }
                for f in schema.fields
            ],
            "estimated_row_count": schema.estimated_row_count,
            "discovered_at": schema.discovered_at,
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{source_id}/preview")
async def preview_source(
    source_id: UUID,
    n: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Return a preview of records from a data source."""
    service = IngestionService(db)
    try:
        records = await service.preview_source(source_id, n=n)
        return {"source_id": str(source_id), "records": records, "count": len(records)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/connectors/marketplace")
async def list_connector_marketplace():
    """List all available connector types with metadata."""
    registry = get_registry()
    return {
        "connectors": registry.list_connectors(),
        "total": len(registry.supported_types()),
    }
