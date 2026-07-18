"""Pipeline Celery Tasks with retry support."""
import httpx
from celery import chain
from app.core.celery_app import celery_app
from app.core.config import settings
import structlog

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_ingestion_task(self, source_id: str, tenant_id: str, options: dict = None):
    """Trigger ingestion for a data source."""
    try:
        with httpx.Client(timeout=300) as client:
            resp = client.post(
                f"{settings.INGESTION_SERVICE_URL}/api/v1/jobs/",
                json={"source_id": source_id, "options": options or {}},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("ingestion_task_failed", source_id=source_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_validation_task(self, records: list, rules: list):
    """Run validation on ingested records."""
    try:
        with httpx.Client(timeout=300) as client:
            resp = client.post(
                f"{settings.VALIDATION_SERVICE_URL}/api/v1/validation/validate",
                json={"records": records, "rules": rules},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_transformation_task(self, records: list, rules: list):
    """Run transformation on validated records."""
    try:
        with httpx.Client(timeout=300) as client:
            resp = client.post(
                f"{settings.TRANSFORMATION_SERVICE_URL}/api/v1/transform/transform",
                json={"records": records, "rules": rules},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        raise self.retry(exc=exc)


def create_pipeline_chain(source_id: str, validation_rules: list, transformation_rules: list):
    """Create a Celery chain for the full ETL pipeline."""
    return chain(
        run_ingestion_task.s(source_id=source_id, tenant_id="default"),
        run_validation_task.s(rules=validation_rules),
        run_transformation_task.s(rules=transformation_rules),
    )
