"""Notification API endpoints — with history persistence and stats."""
from typing import Any
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.channels.notification_channels import NotificationService, NotificationMessage
from app.services.notification_history import NotificationHistoryService, NotificationRecord

router = APIRouter()


class SendNotificationRequest(BaseModel):
    channel: str
    recipient: str
    title: str
    body: str
    severity: str = "info"
    metadata: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = "default"


class BroadcastRequest(BaseModel):
    channels: list[dict[str, str]]
    title: str
    body: str
    severity: str = "info"
    tenant_id: str = "default"


@router.post("/send")
async def send_notification(request: SendNotificationRequest):
    """Send a notification via a single channel (email/slack/teams/webhook)."""
    service = NotificationService()
    history_svc = NotificationHistoryService()
    message = NotificationMessage(
        title=request.title,
        body=request.body,
        severity=request.severity,
        metadata=request.metadata,
    )
    result = await service.send(request.channel, request.recipient, message)
    history_svc.record(NotificationRecord(
        channel=request.channel,
        recipient=request.recipient,
        title=request.title,
        body=request.body,
        severity=request.severity,
        success=result.get("success", False),
        error=result.get("error", ""),
        tenant_id=request.tenant_id,
    ))
    return result


@router.post("/broadcast")
async def broadcast_notification(request: BroadcastRequest):
    """Send a notification to multiple channels simultaneously."""
    service = NotificationService()
    history_svc = NotificationHistoryService()
    message = NotificationMessage(title=request.title, body=request.body, severity=request.severity)
    results = await service.broadcast(request.channels, message)
    for i, result in enumerate(results):
        ch_info = request.channels[i] if i < len(request.channels) else {}
        history_svc.record(NotificationRecord(
            channel=ch_info.get("channel", "unknown"),
            recipient=ch_info.get("recipient", ""),
            title=request.title,
            body=request.body,
            severity=request.severity,
            success=result.get("success", False),
            tenant_id=request.tenant_id,
        ))
    return {
        "results": results,
        "total": len(results),
        "succeeded": sum(1 for r in results if r.get("success")),
    }


@router.get("/channels")
async def list_channels():
    """List all available notification channels."""
    from app.channels.notification_channels import CHANNEL_REGISTRY
    return {"channels": list(CHANNEL_REGISTRY.keys())}


@router.get("/history")
async def get_history(limit: int = Query(50, ge=1, le=200)):
    """Return recent notification history."""
    return {"history": NotificationHistoryService().get_history(limit=limit)}


@router.get("/stats")
async def get_stats():
    """Return notification delivery statistics."""
    return NotificationHistoryService().get_stats()
