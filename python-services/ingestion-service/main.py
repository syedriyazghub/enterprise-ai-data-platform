"""
Ingestion Service - Main Application Entry Point

Handles data ingestion from 50+ heterogeneous sources including
REST APIs, databases, file systems, cloud storage, and message queues.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.telemetry import setup_telemetry
from app.core.middleware import RateLimitMiddleware, RequestIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    setup_logging()
    setup_telemetry(service_name="ingestion-service")
    await init_db()
    yield


def create_app() -> FastAPI:
    """Factory function to create the FastAPI application."""
    app = FastAPI(
        title="Ingestion Service",
        description="Universal data ingestion from 50+ sources",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Prometheus metrics
    Instrumentator().instrument(app).expose(app)

    # Routes
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "service": "ingestion-service", "version": settings.APP_VERSION}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)
