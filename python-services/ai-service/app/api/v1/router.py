"""API v1 router for AI service."""
from fastapi import APIRouter
from app.api.v1 import ai_endpoints

api_router = APIRouter()
api_router.include_router(ai_endpoints.router, prefix="/ai", tags=["AI Features"])
