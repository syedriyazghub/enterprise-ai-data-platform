"""API v1 router for transformation service."""
from fastapi import APIRouter
from app.api.v1 import transform_endpoints

api_router = APIRouter()
api_router.include_router(transform_endpoints.router, prefix="/transform", tags=["Transformation"])
