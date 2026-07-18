"""Analytics API endpoints."""
from fastapi import APIRouter, Query
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/summary")
async def pipeline_summary(
    tenant_id: str = Query("default-tenant"),
    days: int = Query(7, ge=1, le=90),
):
    """Get pipeline execution summary for the last N days."""
    service = AnalyticsService()
    return await service.get_pipeline_summary(tenant_id, days)


@router.get("/quality")
async def quality_metrics(tenant_id: str = Query("default-tenant")):
    """Get data quality metrics aggregated by source type."""
    service = AnalyticsService()
    return await service.get_quality_metrics(tenant_id)


@router.get("/kpis")
async def kpis(tenant_id: str = Query("default-tenant")):
    """Get key performance indicators for the dashboard."""
    service = AnalyticsService()
    return await service.get_kpis(tenant_id)
