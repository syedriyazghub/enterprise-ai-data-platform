"""
Ingestion service background workers.

Celery tasks for async pipeline execution so HTTP endpoints
return immediately (202 Accepted) while work runs in background.
"""
from __future__ import annotations

import structlog
from celery import Celery

from app.core.config import settings

logger = structlog.get_logger()

celery_app = Celery(
    "ingestion-service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.ingestion_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.ingestion_tasks.*": {"queue": "ingestion"},
    },
)
