"""
Ingestion Celery tasks — async background execution.

Tasks:
- run_ingestion_task: runs a single source ingestion job
- run_pipeline_task:  runs the full enterprise pipeline engine
"""
from __future__ import annotations

import structlog
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30, name="ingestion.run_ingestion")
def run_ingestion_task(self, source_id: str, tenant_id: str, options: dict | None = None):
    """
    Run ingestion for a data source asynchronously.
    Called by the scheduling service or triggered manually.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.core.config import settings
    from app.services.ingestion_service import IngestionService
    import uuid

    async def _run():
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as session:
            service = IngestionService(session)
            job = await service.run_ingestion(
                source_id=uuid.UUID(source_id),
                tenant_id=tenant_id,
                options=options or {},
            )
            await session.commit()
            return {"job_id": str(job.id), "status": job.status.value, "records": job.records_ingested}

    try:
        result = asyncio.get_event_loop().run_until_complete(_run())
        logger.info("ingestion_task_completed", source_id=source_id, result=result)
        return result
    except Exception as exc:
        logger.error("ingestion_task_failed", source_id=source_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, name="ingestion.run_pipeline")
def run_pipeline_task(self, pipeline_config: dict):
    """
    Run the full enterprise pipeline engine asynchronously.
    Accepts a serialised PipelineConfig dict.
    """
    import asyncio
    from app.services.pipeline_engine import PipelineEngine, PipelineConfig

    async def _run():
        engine = PipelineEngine()
        config = PipelineConfig(**pipeline_config)
        result = await engine.execute(config)
        return {
            "execution_id": result.execution_id,
            "status": result.status,
            "records": result.total_records_ingested,
            "quality_score": result.quality_score,
            "duration_ms": result.duration_ms,
        }

    try:
        result = asyncio.get_event_loop().run_until_complete(_run())
        logger.info("pipeline_task_completed", pipeline_id=pipeline_config.get("pipeline_id"), result=result)
        return result
    except Exception as exc:
        logger.error("pipeline_task_failed", error=str(exc))
        raise self.retry(exc=exc)
