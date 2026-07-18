"""API v1 router for scheduling service."""
from fastapi import APIRouter
from app.api.v1 import schedule_endpoints

api_router = APIRouter()
api_router.include_router(schedule_endpoints.router, prefix="/schedules", tags=["Scheduling"])
