"""Scheduling API endpoints."""
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.scheduling_service import SchedulingService, PipelineSchedule

router = APIRouter()


class CreateScheduleRequest(BaseModel):
    name: str
    source_id: str
    cron_expression: str = Field(..., examples=["0 */6 * * *"])
    validation_rules: list[dict] = []
    transformation_rules: list[dict] = []


@router.post("/", status_code=201)
async def create_schedule(request: CreateScheduleRequest):
    """Create a new pipeline schedule using a cron expression."""
    service = SchedulingService()
    schedule = PipelineSchedule(
        schedule_id=str(uuid.uuid4()),
        name=request.name,
        source_id=request.source_id,
        cron_expression=request.cron_expression,
        validation_rules=request.validation_rules,
        transformation_rules=request.transformation_rules,
    )
    try:
        result = service.create_schedule(schedule)
        return result.__dict__
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_schedules():
    """List all pipeline schedules."""
    service = SchedulingService()
    return {"schedules": [s.__dict__ for s in service.list_schedules()]}


@router.post("/{schedule_id}/trigger")
async def trigger_schedule(schedule_id: str):
    """Manually trigger a scheduled pipeline."""
    service = SchedulingService()
    try:
        task_id = service.trigger_now(schedule_id)
        return {"schedule_id": schedule_id, "task_id": task_id, "status": "triggered"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
