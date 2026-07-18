"""Pipeline schedule management service."""
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import redis
from croniter import croniter
import structlog

from app.core.config import settings
from app.workers.pipeline_tasks import create_pipeline_chain

logger = structlog.get_logger()


@dataclass
class PipelineSchedule:
    schedule_id: str
    name: str
    source_id: str
    cron_expression: str
    validation_rules: list[dict] = field(default_factory=list)
    transformation_rules: list[dict] = field(default_factory=list)
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_run_at: str | None = None
    next_run_at: str | None = None


class SchedulingService:
    """Manages pipeline schedules stored in Redis."""

    def __init__(self):
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self._key_prefix = "schedule:"

    def create_schedule(self, schedule: PipelineSchedule) -> PipelineSchedule:
        if not croniter.is_valid(schedule.cron_expression):
            raise ValueError(f"Invalid cron expression: {schedule.cron_expression}")
        schedule.next_run_at = self._next_run(schedule.cron_expression)
        self._redis.set(
            f"{self._key_prefix}{schedule.schedule_id}",
            json.dumps(schedule.__dict__),
        )
        logger.info("schedule_created", schedule_id=schedule.schedule_id)
        return schedule

    def get_schedule(self, schedule_id: str) -> PipelineSchedule | None:
        data = self._redis.get(f"{self._key_prefix}{schedule_id}")
        if not data:
            return None
        return PipelineSchedule(**json.loads(data))

    def list_schedules(self) -> list[PipelineSchedule]:
        keys = self._redis.keys(f"{self._key_prefix}*")
        schedules = []
        for key in keys:
            data = self._redis.get(key)
            if data:
                schedules.append(PipelineSchedule(**json.loads(data)))
        return schedules

    def trigger_now(self, schedule_id: str) -> str:
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        task_chain = create_pipeline_chain(
            source_id=schedule.source_id,
            validation_rules=schedule.validation_rules,
            transformation_rules=schedule.transformation_rules,
        )
        result = task_chain.apply_async()
        logger.info("pipeline_triggered", schedule_id=schedule_id, task_id=result.id)
        return result.id

    def _next_run(self, cron_expr: str) -> str:
        cron = croniter(cron_expr, datetime.utcnow())
        return cron.get_next(datetime).isoformat()
