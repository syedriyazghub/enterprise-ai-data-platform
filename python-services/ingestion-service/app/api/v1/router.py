"""API v1 router aggregating all endpoint modules."""
from fastapi import APIRouter
from app.api.v1 import sources, jobs, upload

api_router = APIRouter()
api_router.include_router(sources.router, prefix="/sources", tags=["Data Sources"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Ingestion Jobs"])
api_router.include_router(upload.router, prefix="/upload", tags=["File Upload"])
