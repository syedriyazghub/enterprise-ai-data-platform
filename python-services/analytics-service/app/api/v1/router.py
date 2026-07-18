"""API v1 router for analytics service."""
from fastapi import APIRouter
from app.api.v1 import analytics_endpoints

api_router = APIRouter()
api_router.include_router(analytics_endpoints.router, prefix="/analytics", tags=["Analytics"])
