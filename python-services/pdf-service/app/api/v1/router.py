"""API v1 router for PDF service."""
from fastapi import APIRouter
from app.api.v1 import pdf_endpoints

api_router = APIRouter()
api_router.include_router(pdf_endpoints.router, prefix="/pdf", tags=["PDF Processing"])
