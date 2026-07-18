"""
Enterprise Event Bus

Publishes typed domain events to Kafka (production) with an
in-process async fallback for development/testing.

Events published:
  upload.started / upload.completed
  pipeline.started / pipeline.completed / pipeline.failed
  validation.started / validation.completed
  transformation.started / transformation.completed
  ai.started / ai.completed
  notification.sent
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine

import structlog

logger = structlog.get_logger()


class EventType(str, Enum):
    UPLOAD_STARTED = "upload.started"
    UPLOAD_COMPLETED = "upload.completed"
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"
    VALIDATION_STARTED = "validation.started"
    VALIDATION_COMPLETED = "validation.completed"
    TRANSFORMATION_STARTED = "transformation.started"
    TRANSFORMATION_COMPLETED = "transformation.completed"
    AI_STARTED = "ai.started"
    AI_COMPLETED = "ai.completed"
    NOTIFICATION_SENT = "notification.sent"
    SOURCE_CREATED = "source.created"
    SOURCE_DELETED = "source.deleted"
    SCHEMA_DETECTED = "schema.detected"
    ANOMALY_DETECTED = "anomaly.detected"


@dataclass
class PlatformEvent:
    event_type: EventType
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default"
    timestamp: float = field(default_factory=time.time)
    correlation_id: str = ""
    service: str = ""

    def to_json(self) -> str:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return json.dumps(d, default=str)

    @classmethod
    def from_json(cls, raw: str) -> "PlatformEvent":
        d = json.loads(raw)
        d["event_type"] = EventType(d["event_type"])
        return cls(**d)


# ── Subscriber registry ───────────────────────────────────────────────────────

Handler = Callable[[PlatformEvent], Coroutine[Any, Any, None]]
_subscribers: dict[EventType, list[Handler]] = {}


def subscribe(event_type: EventType):
    """Decorator to register an async handler for an event type."""
    def decorator(fn: Handler) -> Handler:
        _subscribers.setdefault(event_type, []).append(fn)
        return fn
    return decorator


async def _dispatch_local(event: PlatformEvent) -> None:
    handlers = _subscribers.get(event.event_type, [])
    if handlers:
        await asyncio.gather(*[h(event) for h in handlers], return_exceptions=True)


# ── Event Bus ─────────────────────────────────────────────────────────────────

class EventBus:
    """
    Publishes events to Kafka with in-process fallback.
    Singleton — use get_event_bus().
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092", topic_prefix: str = "platform"):
        self._bootstrap_servers = bootstrap_servers
        self._topic_prefix = topic_prefix
        self._producer = None

    async def _get_producer(self):
        if self._producer is None:
            try:
                from aiokafka import AIOKafkaProducer
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=self._bootstrap_servers,
                    value_serializer=lambda v: v.encode("utf-8"),
                    acks="all",
                    enable_idempotence=True,
                )
                await self._producer.start()
            except Exception as exc:
                logger.warning("kafka_producer_unavailable", error=str(exc))
                self._producer = None
        return self._producer

    async def publish(self, event: PlatformEvent) -> None:
        """Publish event to Kafka and dispatch to local subscribers."""
        topic = f"{self._topic_prefix}.{event.event_type.value.replace('.', '-')}"
        logger.info(
            "event_published",
            event_type=event.event_type.value,
            event_id=event.event_id,
            tenant_id=event.tenant_id,
        )
        producer = await self._get_producer()
        if producer:
            try:
                await producer.send_and_wait(topic, event.to_json())
            except Exception as exc:
                logger.warning("kafka_publish_failed", error=str(exc), event_type=event.event_type.value)

        # Always dispatch locally regardless of Kafka availability
        await _dispatch_local(event)

    async def close(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None


# ── Singleton ─────────────────────────────────────────────────────────────────

_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        try:
            from app.core.config import settings
            _bus = EventBus(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                topic_prefix="platform",
            )
        except Exception:
            _bus = EventBus()
    return _bus


async def publish_event(
    event_type: EventType,
    payload: dict[str, Any],
    tenant_id: str = "default",
    correlation_id: str = "",
    service: str = "",
) -> None:
    """Convenience function to publish a platform event."""
    event = PlatformEvent(
        event_type=event_type,
        payload=payload,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        service=service,
    )
    await get_event_bus().publish(event)
