"""API v1 router for validation service."""
from fastapi import APIRouter
from app.api.v1 import validation
from app.api.v1 import business_rules_endpoints

api_router = APIRouter()
api_router.include_router(validation.router, prefix="/validation", tags=["Validation"])
api_router.include_router(business_rules_endpoints.router, prefix="/rules", tags=["Business Rules"])
