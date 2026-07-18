"""
Unit tests for ingestion service:
- BaseConnector interface
- ConnectorRegistry
- File connectors (CSV, JSON)
- IngestionService helpers
"""
import io
import json
import os
import tempfile
import pytest

from app.connectors.base import ConnectorConfig, IngestedRecord, ConnectorHealth
from app.connectors.registry import ConnectorRegistry, get_connector
from app.connectors.file.file_connectors import CSVConnector, JSONConnector
from app.models.pg_models import SourceType
from app.services.ingestion_service import IngestionService


# ── ConnectorRegistry ─────────────────────────────────────────────────────────

class TestConnectorRegistry:
    def setup_method(self):
        self.registry = ConnectorRegistry()

    def test_all_builtin_types_registered(self):
        supported = self.registry.supported_types()
        for expected in ["csv", "excel", "json", "xml", "parquet", "postgresql",
                         "mongodb", "rest_api", "graphql", "aws_s3", "azure_blob",
                         "kafka", "rabbitmq"]:
            assert expected in supported

    def test_get_csv_connector(self):
        config = ConnectorConfig(source_type="csv", connection_params={"file_path": "/tmp/test.csv"})
        connector = self.registry.get(SourceType.CSV, config)
        assert isinstance(connector, CSVConnector)

    def test_get_unknown_type_raises(self):
        with pytest.raises(ValueError, match="No connector registered"):
            config = ConnectorConfig(source_type="unknown_type")
            # Use a fake SourceType value
            from unittest.mock import MagicMock
            fake_type = MagicMock()
            fake_type.value = "unknown_type"
            self.registry.get(fake_type, config)

    def test_list_connectors_returns_metadata(self):
        connectors = self.registry.list_connectors()
        assert len(connectors) >= 13
        for c in connectors:
            assert "source_type" in c
            assert "name" in c
            assert "version" in c

    def test_is_registered(self):
        assert self.registry.is_registered(SourceType.CSV) is True

    def test_register_custom_connector(self):
        from app.connectors.base import BaseConnector
        from typing import AsyncIterator

        class MyConnector(BaseConnector):
            async def connect(self): pass
            async def disconnect(self): pass
            async def test_connection(self): return True
            async def fetch(self) -> AsyncIterator[IngestedRecord]:
                yield IngestedRecord(data={"custom": "data"})

        self.registry.register(SourceType.WEBHOOK, MyConnector)
        assert self.registry.is_registered(SourceType.WEBHOOK)


# ── CSVConnector ──────────────────────────────────────────────────────────────

class TestCSVConnector:
    @pytest.fixture
    def csv_file(self, tmp_path):
        f = tmp_path / "test.csv"
        f.write_text("name,age,email\nAlice,25,alice@example.com\nBob,30,bob@example.com\n")
        return str(f)

    @pytest.mark.asyncio
    async def test_fetch_returns_records(self, csv_file):
        config = ConnectorConfig(source_type="csv", connection_params={"file_path": csv_file})
        connector = CSVConnector(config)
        async with connector:
            records = [r async for r in connector.fetch()]
        assert len(records) == 2
        assert records[0].data["name"] == "Alice"
        assert records[1].data["name"] == "Bob"

    @pytest.mark.asyncio
    async def test_test_connection_existing_file(self, csv_file):
        config = ConnectorConfig(source_type="csv", connection_params={"file_path": csv_file})
        connector = CSVConnector(config)
        await connector.connect()
        assert await connector.test_connection() is True
        await connector.disconnect()

    @pytest.mark.asyncio
    async def test_test_connection_missing_file(self):
        config = ConnectorConfig(source_type="csv", connection_params={"file_path": "/nonexistent/file.csv"})
        connector = CSVConnector(config)
        await connector.connect()
        assert await connector.test_connection() is False

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self, csv_file):
        config = ConnectorConfig(source_type="csv", connection_params={"file_path": csv_file})
        connector = CSVConnector(config)
        await connector.connect()
        health = await connector.health()
        assert isinstance(health, ConnectorHealth)
        assert health.healthy is True
        assert health.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_sample_returns_n_records(self, csv_file):
        config = ConnectorConfig(source_type="csv", connection_params={"file_path": csv_file})
        connector = CSVConnector(config)
        async with connector:
            samples = await connector.sample(n=1)
        assert len(samples) == 1

    @pytest.mark.asyncio
    async def test_preview_returns_dicts(self, csv_file):
        config = ConnectorConfig(source_type="csv", connection_params={"file_path": csv_file})
        connector = CSVConnector(config)
        async with connector:
            preview = await connector.preview(n=2)
        assert isinstance(preview, list)
        assert all(isinstance(r, dict) for r in preview)

    @pytest.mark.asyncio
    async def test_discover_schema(self, csv_file):
        config = ConnectorConfig(source_type="csv", connection_params={"file_path": csv_file})
        connector = CSVConnector(config)
        async with connector:
            schema = await connector.discover_schema()
        field_names = [f.name for f in schema.fields]
        assert "name" in field_names
        assert "age" in field_names
        assert "email" in field_names

    @pytest.mark.asyncio
    async def test_source_metadata_populated(self, csv_file):
        config = ConnectorConfig(source_type="csv", connection_params={"file_path": csv_file})
        connector = CSVConnector(config)
        async with connector:
            records = [r async for r in connector.fetch()]
        assert records[0].source_metadata["source_type"] == "csv"


# ── JSONConnector ─────────────────────────────────────────────────────────────

class TestJSONConnector:
    @pytest.fixture
    def json_file(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text(json.dumps([
            {"id": 1, "product": "Widget", "price": 9.99},
            {"id": 2, "product": "Gadget", "price": 19.99},
        ]))
        return str(f)

    @pytest.mark.asyncio
    async def test_fetch_list(self, json_file):
        config = ConnectorConfig(source_type="json", connection_params={"file_path": json_file})
        connector = JSONConnector(config)
        async with connector:
            records = [r async for r in connector.fetch()]
        assert len(records) == 2
        assert records[0].data["product"] == "Widget"

    @pytest.mark.asyncio
    async def test_fetch_single_object(self, tmp_path):
        f = tmp_path / "single.json"
        f.write_text(json.dumps({"key": "value"}))
        config = ConnectorConfig(source_type="json", connection_params={"file_path": str(f)})
        connector = JSONConnector(config)
        async with connector:
            records = [r async for r in connector.fetch()]
        assert len(records) == 1
        assert records[0].data["key"] == "value"


# ── IngestionService helpers ──────────────────────────────────────────────────

class TestIngestionServiceHelpers:
    def setup_method(self):
        # Use a mock DB session — we only test pure methods
        self.service = IngestionService(db=None)

    def test_compute_checksum_deterministic(self):
        records = [{"a": 1}, {"b": 2}]
        c1 = self.service._compute_checksum(records)
        c2 = self.service._compute_checksum(records)
        assert c1 == c2
        assert len(c1) == 64  # SHA-256 hex

    def test_compute_checksum_different_for_different_data(self):
        c1 = self.service._compute_checksum([{"a": 1}])
        c2 = self.service._compute_checksum([{"a": 2}])
        assert c1 != c2
