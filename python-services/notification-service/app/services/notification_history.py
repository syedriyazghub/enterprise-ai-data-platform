"""
Notification history and audit service.

Persists every sent notification to Redis with TTL for audit trail.
Provides history retrieval and statistics.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

import structlog

from app.core.config import settings

logger = structlog.get_logger()

_HISTORY_KEY = "notifications:history"
_HISTORY_TTL = 60 * 60 * 24 * 30  # 30 days


@dataclass
class NotificationRecord:
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    channel: str = ""
    recipient: str = ""
    title: str = ""
    body: str = ""
    severity: str = "info"
    success: bool = False
    error: str = ""
    tenant_id: str = "default"
    timestamp: float = field(default_factory=time.time)


class NotificationHistoryService:
    """Stores and retrieves notification history from Redis."""

    def __init__(self):
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            try:
                import redis as redis_lib
                self._redis = redis_lib.from_url(
                    settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2
                )
                self._redis.ping()
            except Exception as exc:
                logger.warning("notification_redis_unavailable", error=str(exc))
                self._redis = None
        return self._redis

    def record(self, record: NotificationRecord) -> None:
        """Persist a notification record to Redis."""
        r = self._get_redis()
        if not r:
            return
        try:
            r.lpush(_HISTORY_KEY, json.dumps(asdict(record)))
            r.ltrim(_HISTORY_KEY, 0, 999)   # keep last 1000
            r.expire(_HISTORY_KEY, _HISTORY_TTL)
        except Exception as exc:
            logger.warning("notification_record_failed", error=str(exc))

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the most recent notification records."""
        r = self._get_redis()
        if not r:
            return []
        try:
            raw = r.lrange(_HISTORY_KEY, 0, limit - 1)
            return [json.loads(item) for item in raw]
        except Exception:
            return []

    def get_stats(self) -> dict[str, Any]:
        """Return aggregate statistics for sent notifications."""
        history = self.get_history(limit=1000)
        if not history:
            return {"total": 0, "succeeded": 0, "failed": 0, "by_channel": {}}

        by_channel: dict[str, int] = {}
        succeeded = 0
        for record in history:
            ch = record.get("channel", "unknown")
            by_channel[ch] = by_channel.get(ch, 0) + 1
            if record.get("success"):
                succeeded += 1

        return {
            "total": len(history),
            "succeeded": succeeded,
            "failed": len(history) - succeeded,
            "success_rate": round(succeeded / len(history) * 100, 1),
            "by_channel": by_channel,
        }
