"""
Messaging connectors: Apache Kafka, RabbitMQ.

Both connectors support:
- Connection testing
- Schema discovery (from message samples)
- Streaming fetch with configurable batch sizes
- Graceful disconnect
"""
from __future__ import annotations

import json
from typing import AsyncIterator
import structlog

from app.connectors.base import BaseConnector, ConnectorConfig, IngestedRecord, ConnectorMetadata

logger = structlog.get_logger()


class KafkaConnector(BaseConnector):
    """Ingests messages from Apache Kafka topics."""

    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            name="KafkaConnector",
            version="1.0.0",
            source_type="kafka",
            description="Ingest messages from Apache Kafka topics",
            supports_streaming=True,
            supports_schema_discovery=True,
            required_params=["bootstrap_servers", "topic"],
            optional_params=["group_id", "auto_offset_reset", "max_messages", "timeout_ms"],
        )

    async def connect(self) -> None:
        from aiokafka import AIOKafkaConsumer
        params = self.config.connection_params
        self._consumer = AIOKafkaConsumer(
            params["topic"],
            bootstrap_servers=params.get("bootstrap_servers", "localhost:9092"),
            group_id=params.get("group_id", "platform-ingestion"),
            auto_offset_reset=params.get("auto_offset_reset", "earliest"),
            value_deserializer=lambda m: json.loads(m.decode("utf-8", errors="replace")),
            enable_auto_commit=True,
        )
        await self._consumer.start()
        logger.info("kafka_connected", topic=params["topic"])

    async def disconnect(self) -> None:
        if hasattr(self, "_consumer"):
            await self._consumer.stop()

    async def test_connection(self) -> bool:
        try:
            _ = self._consumer.assignment()
            return True
        except Exception as exc:
            logger.error("kafka_test_failed", error=str(exc))
            return False

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        params = self.config.connection_params
        max_messages = self.config.options.get("max_messages", 1000)
        topic = params["topic"]
        count = 0
        async for msg in self._consumer:
            data = msg.value if isinstance(msg.value, dict) else {"value": msg.value}
            yield IngestedRecord(
                data=data,
                source_metadata={
                    "source_type": "kafka",
                    "topic": topic,
                    "partition": msg.partition,
                    "offset": msg.offset,
                    "timestamp": msg.timestamp,
                },
            )
            count += 1
            if count >= max_messages:
                break


class RabbitMQConnector(BaseConnector):
    """Ingests messages from RabbitMQ queues."""

    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            name="RabbitMQConnector",
            version="1.0.0",
            source_type="rabbitmq",
            description="Ingest messages from RabbitMQ queues",
            supports_streaming=True,
            supports_schema_discovery=True,
            required_params=["url", "queue"],
            optional_params=["max_messages", "prefetch_count"],
        )

    async def connect(self) -> None:
        import aio_pika
        params = self.config.connection_params
        self._connection = await aio_pika.connect_robust(
            params.get("url", "amqp://guest:guest@localhost/")
        )
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=self.config.options.get("prefetch_count", 100))
        self._queue = await self._channel.declare_queue(params["queue"], durable=True, passive=True)
        logger.info("rabbitmq_connected", queue=params["queue"])

    async def disconnect(self) -> None:
        if hasattr(self, "_connection") and not self._connection.is_closed:
            await self._connection.close()

    async def test_connection(self) -> bool:
        try:
            return not self._connection.is_closed
        except Exception:
            return False

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        params = self.config.connection_params
        max_messages = self.config.options.get("max_messages", 1000)
        queue_name = params["queue"]
        count = 0
        async with self._queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        body = message.body.decode("utf-8", errors="replace")
                        data = json.loads(body) if body.startswith(("{", "[")) else {"raw": body}
                        records = data if isinstance(data, list) else [data]
                        for item in records:
                            yield IngestedRecord(
                                data=item if isinstance(item, dict) else {"value": item},
                                source_metadata={"source_type": "rabbitmq", "queue": queue_name},
                            )
                            count += 1
                            if count >= max_messages:
                                return
                    except json.JSONDecodeError:
                        yield IngestedRecord(
                            data={"raw": message.body.decode("utf-8", errors="replace")},
                            source_metadata={"source_type": "rabbitmq", "queue": queue_name},
                        )
                        count += 1
                if count >= max_messages:
                    break
