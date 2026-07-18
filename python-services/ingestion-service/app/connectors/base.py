"""
Enterprise Connector SDK — Base interface for all data source connectors.

Every connector must implement this interface. Supports:
- Async context manager lifecycle
- Schema discovery
- Sample/preview data
- Health checks
- Streaming + batch fetch
- Connector metadata
- Retry-aware connection
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class ConnectorConfig:
    """Generic connector configuration."""
    source_type: str
    connection_params: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestedRecord:
    """Represents a single ingested record."""
    data: dict[str, Any]
    source_metadata: dict[str, Any] = field(default_factory=dict)
    raw_content: bytes | None = None


@dataclass
class ConnectorMetadata:
    """Describes a connector's capabilities and identity."""
    name: str
    version: str
    source_type: str
    description: str
    author: str = "platform"
    supports_streaming: bool = False
    supports_schema_discovery: bool = False
    supports_preview: bool = True
    required_params: list[str] = field(default_factory=list)
    optional_params: list[str] = field(default_factory=list)


@dataclass
class FieldDescriptor:
    """Describes a single field in a discovered schema."""
    name: str
    data_type: str
    nullable: bool = True
    description: str = ""
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class DiscoveredSchema:
    """Schema discovered from a data source."""
    fields: list[FieldDescriptor]
    estimated_row_count: int = 0
    source_name: str = ""
    discovered_at: float = field(default_factory=time.time)


@dataclass
class ConnectorHealth:
    """Health status of a connector."""
    healthy: bool
    latency_ms: float
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors.

    Lifecycle:
        async with connector:
            schema = await connector.discover_schema()
            samples = await connector.sample(n=10)
            async for record in connector.stream():
                process(record)
    """

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._connected: bool = False

    # ── Required lifecycle ────────────────────────────────────────────────────

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the data source."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the data source."""

    @abstractmethod
    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        """Fetch all records from the data source as an async stream."""

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the connection is valid."""

    # ── Optional enrichment methods (override in subclasses) ─────────────────

    async def health(self) -> ConnectorHealth:
        """Return health status with latency measurement."""
        start = time.monotonic()
        try:
            ok = await self.test_connection()
            latency = (time.monotonic() - start) * 1000
            return ConnectorHealth(healthy=ok, latency_ms=round(latency, 2))
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            return ConnectorHealth(healthy=False, latency_ms=round(latency, 2), message=str(exc))

    async def discover_schema(self) -> DiscoveredSchema:
        """Discover schema by sampling records. Override for native schema APIs."""
        samples = await self.sample(n=100)
        if not samples:
            return DiscoveredSchema(fields=[], source_name=self.config.source_type)

        all_keys: set[str] = set()
        for r in samples:
            all_keys.update(r.data.keys())

        fields = []
        for key in sorted(all_keys):
            values = [r.data.get(key) for r in samples if r.data.get(key) is not None]
            fields.append(FieldDescriptor(
                name=key,
                data_type=self._infer_type(values),
                nullable=any(r.data.get(key) is None for r in samples),
                sample_values=values[:3],
            ))

        return DiscoveredSchema(
            fields=fields,
            estimated_row_count=len(samples),
            source_name=self.config.source_type,
        )

    async def sample(self, n: int = 10) -> list[IngestedRecord]:
        """Return up to n sample records."""
        records: list[IngestedRecord] = []
        async for record in self.fetch():
            records.append(record)
            if len(records) >= n:
                break
        return records

    async def preview(self, n: int = 5) -> list[dict[str, Any]]:
        """Return preview data as plain dicts."""
        samples = await self.sample(n)
        return [r.data for r in samples]

    def metadata(self) -> ConnectorMetadata:
        """Return connector metadata. Override to provide rich metadata."""
        return ConnectorMetadata(
            name=self.__class__.__name__,
            version="1.0.0",
            source_type=self.config.source_type,
            description=self.__class__.__doc__ or "",
        )

    # ── Context manager ───────────────────────────────────────────────────────

    async def __aenter__(self) -> "BaseConnector":
        await self.connect()
        self._connected = True
        return self

    async def __aexit__(self, *args) -> None:
        await self.disconnect()
        self._connected = False

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _infer_type(self, values: list[Any]) -> str:
        if not values:
            return "unknown"
        import re
        date_re = re.compile(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}")
        for v in values[:10]:
            s = str(v)
            try:
                int(s)
                return "integer"
            except ValueError:
                pass
            try:
                float(s)
                return "float"
            except ValueError:
                pass
            if date_re.match(s):
                return "date"
            if s.lower() in ("true", "false"):
                return "boolean"
        return "string"
