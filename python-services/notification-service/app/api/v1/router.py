"""API v1 router for notification service."""
from fastapi import APIRouter
from app.api.v1 import notification_endpoints

api_router = APIRouter()
api_router.include_router(notification_endpoints.router, prefix="/notifications", tags=["Notifications"])
