"""
Multi-channel notification service.
Supports Email, Slack, Microsoft Teams, and Webhooks.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


@dataclass
class NotificationMessage:
    title: str
    body: str
    severity: str = "info"  # info | warning | error | success
    metadata: dict = None


class BaseNotificationChannel(ABC):
    @abstractmethod
    async def send(self, message: NotificationMessage, recipient: str) -> bool:
        pass


class EmailChannel(BaseNotificationChannel):
    """Send notifications via SMTP email."""

    async def send(self, message: NotificationMessage, recipient: str) -> bool:
        if not settings.SMTP_USER:
            logger.warning("email_not_configured")
            return False
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{message.severity.upper()}] {message.title}"
            msg["From"] = settings.SMTP_FROM
            msg["To"] = recipient
            msg.attach(MIMEText(message.body, "plain"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            logger.info("email_sent", recipient=recipient)
            return True
        except Exception as e:
            logger.error("email_send_failed", error=str(e))
            return False


class SlackChannel(BaseNotificationChannel):
    """Send notifications to Slack via webhook."""

    async def send(self, message: NotificationMessage, recipient: str) -> bool:
        webhook_url = settings.SLACK_WEBHOOK_URL or recipient
        if not webhook_url:
            return False
        color_map = {"info": "#36a64f", "warning": "#ff9900", "error": "#ff0000", "success": "#36a64f"}
        payload = {
            "attachments": [{
                "color": color_map.get(message.severity, "#36a64f"),
                "title": message.title,
                "text": message.body,
                "footer": "AI Data Platform",
            }]
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook_url, json=payload)
            return resp.status_code == 200


class TeamsChannel(BaseNotificationChannel):
    """Send notifications to Microsoft Teams via webhook."""

    async def send(self, message: NotificationMessage, recipient: str) -> bool:
        webhook_url = settings.TEAMS_WEBHOOK_URL or recipient
        if not webhook_url:
            return False
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": message.title,
            "sections": [{"activityTitle": message.title, "activityText": message.body}],
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook_url, json=payload)
            return resp.status_code == 200


class WebhookChannel(BaseNotificationChannel):
    """Send notifications to a generic webhook URL."""

    async def send(self, message: NotificationMessage, recipient: str) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.post(recipient, json={
                "title": message.title,
                "body": message.body,
                "severity": message.severity,
                "metadata": message.metadata or {},
            })
            return resp.status_code < 300


CHANNEL_REGISTRY: dict[str, BaseNotificationChannel] = {
    "email": EmailChannel(),
    "slack": SlackChannel(),
    "teams": TeamsChannel(),
    "webhook": WebhookChannel(),
}


class NotificationService:
    """Dispatches notifications to one or more channels."""

    async def send(self, channel: str, recipient: str, message: NotificationMessage) -> dict:
        handler = CHANNEL_REGISTRY.get(channel)
        if not handler:
            return {"success": False, "error": f"Unknown channel: {channel}"}
        success = await handler.send(message, recipient)
        return {"success": success, "channel": channel, "recipient": recipient}

    async def broadcast(self, channels: list[dict], message: NotificationMessage) -> list[dict]:
        """Send to multiple channels simultaneously."""
        import asyncio
        tasks = [self.send(c["channel"], c["recipient"], message) for c in channels]
        return await asyncio.gather(*tasks)
