"""
Enterprise Connector Plugin Registry

Supports:
- Static registration of built-in connectors
- Dynamic plugin loading from external modules
- Connector versioning and metadata
- Connector discovery and marketplace listing
- Health-check aggregation across all connectors
"""
from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Type

from app.connectors.base import BaseConnector, ConnectorConfig, ConnectorMetadata
from app.models.pg_models import SourceType

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """
    Central registry for all connector plugins.

    Usage:
        registry = ConnectorRegistry()
        connector = registry.get(SourceType.CSV, config)
        all_meta = registry.list_connectors()
    """

    def __init__(self):
        self._registry: dict[SourceType, Type[BaseConnector]] = {}
        self._metadata_cache: dict[SourceType, ConnectorMetadata] = {}
        self._load_builtins()

    def _load_builtins(self) -> None:
        """Register all built-in connectors."""
        from app.connectors.file.file_connectors import (
            CSVConnector, ExcelConnector, JSONConnector,
            XMLConnector, ParquetConnector,
        )
        from app.connectors.database.db_connectors import (
            PostgreSQLConnector, MongoDBConnector,
        )
        from app.connectors.api.api_connectors import (
            RESTAPIConnector, GraphQLConnector,
        )
        from app.connectors.cloud.cloud_connectors import (
            S3Connector, AzureBlobConnector,
        )
        from app.connectors.messaging.messaging_connectors import (
            KafkaConnector, RabbitMQConnector,
        )

        builtins: list[tuple[SourceType, Type[BaseConnector]]] = [
            (SourceType.CSV,        CSVConnector),
            (SourceType.EXCEL,      ExcelConnector),
            (SourceType.JSON,       JSONConnector),
            (SourceType.XML,        XMLConnector),
            (SourceType.PARQUET,    ParquetConnector),
            (SourceType.POSTGRESQL, PostgreSQLConnector),
            (SourceType.MONGODB,    MongoDBConnector),
            (SourceType.REST_API,   RESTAPIConnector),
            (SourceType.GRAPHQL,    GraphQLConnector),
            (SourceType.AWS_S3,     S3Connector),
            (SourceType.AZURE_BLOB, AzureBlobConnector),
            (SourceType.KAFKA,      KafkaConnector),
            (SourceType.RABBITMQ,   RabbitMQConnector),
        ]
        for source_type, cls in builtins:
            self.register(source_type, cls)

    def register(self, source_type: SourceType, connector_class: Type[BaseConnector]) -> None:
        """Register a connector class for a source type."""
        self._registry[source_type] = connector_class
        logger.debug("connector_registered", extra={"source_type": source_type.value, "class": connector_class.__name__})

    def get(self, source_type: SourceType, config: ConnectorConfig) -> BaseConnector:
        """Instantiate and return a connector for the given source type."""
        connector_class = self._registry.get(source_type)
        if not connector_class:
            available = [s.value for s in self._registry]
            raise ValueError(
                f"No connector registered for source type '{source_type.value}'. "
                f"Available: {available}"
            )
        return connector_class(config)

    def list_connectors(self) -> list[dict]:
        """Return marketplace-style listing of all registered connectors."""
        result = []
        for source_type, cls in self._registry.items():
            try:
                dummy_config = ConnectorConfig(source_type=source_type.value)
                meta = cls(dummy_config).metadata()
            except Exception:
                meta = ConnectorMetadata(
                    name=cls.__name__,
                    version="1.0.0",
                    source_type=source_type.value,
                    description=cls.__doc__ or "",
                )
            result.append({
                "source_type": source_type.value,
                "name": meta.name,
                "version": meta.version,
                "description": meta.description,
                "author": meta.author,
                "supports_streaming": meta.supports_streaming,
                "supports_schema_discovery": meta.supports_schema_discovery,
                "required_params": meta.required_params,
                "optional_params": meta.optional_params,
            })
        return sorted(result, key=lambda x: x["source_type"])

    def load_plugin(self, module_path: str, source_type: SourceType) -> None:
        """
        Dynamically load a connector plugin from a Python module path.

        Example:
            registry.load_plugin("my_plugins.salesforce_connector", SourceType.REST_API)
        """
        try:
            module = importlib.import_module(module_path)
            connector_class = getattr(module, "Connector", None)
            if connector_class is None:
                raise AttributeError(f"Module '{module_path}' must expose a class named 'Connector'")
            if not issubclass(connector_class, BaseConnector):
                raise TypeError(f"'Connector' in '{module_path}' must subclass BaseConnector")
            self.register(source_type, connector_class)
            logger.info("plugin_loaded", extra={"module": module_path, "source_type": source_type.value})
        except Exception as exc:
            logger.error("plugin_load_failed", extra={"module": module_path, "error": str(exc)})
            raise

    def load_plugin_from_file(self, file_path: str, source_type: SourceType) -> None:
        """Load a connector plugin from a .py file path."""
        path = Path(file_path)
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        connector_class = getattr(module, "Connector")
        self.register(source_type, connector_class)

    def is_registered(self, source_type: SourceType) -> bool:
        return source_type in self._registry

    def supported_types(self) -> list[str]:
        return [s.value for s in self._registry]


# ── Singleton registry instance ───────────────────────────────────────────────
_registry: ConnectorRegistry | None = None


def get_registry() -> ConnectorRegistry:
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
    return _registry


def get_connector(source_type: SourceType, config: ConnectorConfig) -> BaseConnector:
    """Convenience factory — backward-compatible with existing code."""
    return get_registry().get(source_type, config)
