"""
Metadata Catalog & Data Lineage Service

Automatically registers:
- Datasets (source, schema, owner, domain, tags)
- Column-level metadata (type, description, quality)
- Pipeline lineage (source → transformation → destination)
- Schema versions with diff tracking
- Quality scores per dataset
- Business definitions

Stored in MongoDB for flexible schema evolution.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import structlog
from beanie import Document, Indexed
from pydantic import Field

logger = structlog.get_logger()


# ── MongoDB Documents ─────────────────────────────────────────────────────────

class DatasetCatalogEntry(Document):
    """Catalog entry for a registered dataset."""

    dataset_id: Indexed(str, unique=True)
    tenant_id: Indexed(str)
    name: str
    description: str = ""
    source_type: str
    source_id: str
    owner: str = ""
    domain: str = ""
    tags: list[str] = Field(default_factory=list)
    columns: list[dict[str, Any]] = Field(default_factory=list)
    schema_version: int = 1
    record_count: int = 0
    quality_score: float = 0.0
    last_ingested_at: Optional[datetime] = None
    business_definitions: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "dataset_catalog"
        indexes = ["tenant_id", "source_type", "domain", "tags"]


class LineageNode(Document):
    """A node in the data lineage graph (source, transform, or destination)."""

    node_id: Indexed(str, unique=True)
    tenant_id: Indexed(str)
    node_type: str          # "source" | "transformation" | "destination"
    name: str
    service: str            # which microservice owns this node
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "lineage_nodes"


class LineageEdge(Document):
    """A directed edge in the lineage graph: from_node → to_node."""

    edge_id: Indexed(str, unique=True)
    tenant_id: Indexed(str)
    from_node_id: str
    to_node_id: str
    job_id: str = ""
    pipeline_id: str = ""
    transformation_type: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "lineage_edges"


class SchemaVersion(Document):
    """Tracks schema versions for drift detection."""

    dataset_id: Indexed(str)
    tenant_id: Indexed(str)
    version: int
    fields: list[dict[str, Any]] = Field(default_factory=list)
    diff_from_previous: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "schema_versions"
        indexes = ["dataset_id", "version"]


# ── Catalog Service ───────────────────────────────────────────────────────────

class MetadataCatalogService:
    """
    Registers and queries dataset metadata and lineage.
    All methods are async and use Beanie ODM.
    """

    async def register_dataset(
        self,
        tenant_id: str,
        source_id: str,
        source_type: str,
        name: str,
        columns: list[dict],
        record_count: int = 0,
        quality_score: float = 0.0,
        owner: str = "",
        domain: str = "",
        tags: list[str] | None = None,
    ) -> DatasetCatalogEntry:
        """Register or update a dataset in the catalog."""
        dataset_id = f"{tenant_id}:{source_id}"
        existing = await DatasetCatalogEntry.find_one(
            DatasetCatalogEntry.dataset_id == dataset_id
        )

        if existing:
            # Detect schema drift
            old_fields = {c["name"] for c in existing.columns}
            new_fields = {c["name"] for c in columns}
            drift = {
                "added": list(new_fields - old_fields),
                "removed": list(old_fields - new_fields),
            }
            existing.columns = columns
            existing.record_count = record_count
            existing.quality_score = quality_score
            existing.last_ingested_at = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            existing.schema_version += 1 if drift["added"] or drift["removed"] else 0
            await existing.save()

            # Save schema version snapshot
            await SchemaVersion(
                dataset_id=dataset_id,
                tenant_id=tenant_id,
                version=existing.schema_version,
                fields=columns,
                diff_from_previous=drift,
            ).insert()

            logger.info("dataset_catalog_updated", dataset_id=dataset_id)
            return existing

        entry = DatasetCatalogEntry(
            dataset_id=dataset_id,
            tenant_id=tenant_id,
            name=name,
            source_type=source_type,
            source_id=source_id,
            columns=columns,
            record_count=record_count,
            quality_score=quality_score,
            owner=owner,
            domain=domain,
            tags=tags or [],
            last_ingested_at=datetime.utcnow(),
        )
        await entry.insert()

        await SchemaVersion(
            dataset_id=dataset_id,
            tenant_id=tenant_id,
            version=1,
            fields=columns,
        ).insert()

        logger.info("dataset_catalog_registered", dataset_id=dataset_id)
        return entry

    async def get_dataset(self, tenant_id: str, source_id: str) -> DatasetCatalogEntry | None:
        return await DatasetCatalogEntry.find_one(
            DatasetCatalogEntry.dataset_id == f"{tenant_id}:{source_id}"
        )

    async def list_datasets(
        self, tenant_id: str, domain: str = "", tag: str = ""
    ) -> list[DatasetCatalogEntry]:
        query = DatasetCatalogEntry.find(DatasetCatalogEntry.tenant_id == tenant_id)
        if domain:
            query = query.find(DatasetCatalogEntry.domain == domain)
        if tag:
            query = query.find({"tags": tag})
        return await query.to_list()

    async def search_datasets(self, tenant_id: str, q: str) -> list[DatasetCatalogEntry]:
        """Simple text search across name, description, tags."""
        all_datasets = await self.list_datasets(tenant_id)
        q_lower = q.lower()
        return [
            d for d in all_datasets
            if q_lower in d.name.lower()
            or q_lower in d.description.lower()
            or any(q_lower in t.lower() for t in d.tags)
        ]

    async def get_schema_history(self, tenant_id: str, source_id: str) -> list[SchemaVersion]:
        dataset_id = f"{tenant_id}:{source_id}"
        return await SchemaVersion.find(
            SchemaVersion.dataset_id == dataset_id
        ).sort("-version").to_list()

    # ── Lineage ───────────────────────────────────────────────────────────────

    async def record_lineage(
        self,
        tenant_id: str,
        job_id: str,
        source_node: dict,
        destination_node: dict,
        transformation_nodes: list[dict] | None = None,
    ) -> None:
        """Record a complete lineage chain for a pipeline execution."""
        import uuid as _uuid

        async def ensure_node(node_data: dict) -> LineageNode:
            node_id = node_data.get("node_id") or str(_uuid.uuid4())
            existing = await LineageNode.find_one(LineageNode.node_id == node_id)
            if existing:
                return existing
            node = LineageNode(
                node_id=node_id,
                tenant_id=tenant_id,
                node_type=node_data["node_type"],
                name=node_data["name"],
                service=node_data.get("service", ""),
                metadata=node_data.get("metadata", {}),
            )
            await node.insert()
            return node

        src = await ensure_node(source_node)
        dst = await ensure_node(destination_node)
        transforms = [await ensure_node(t) for t in (transformation_nodes or [])]

        # Build edge chain: src → t1 → t2 → ... → dst
        chain = [src] + transforms + [dst]
        for i in range(len(chain) - 1):
            edge = LineageEdge(
                edge_id=str(_uuid.uuid4()),
                tenant_id=tenant_id,
                from_node_id=chain[i].node_id,
                to_node_id=chain[i + 1].node_id,
                job_id=job_id,
            )
            await edge.insert()

        logger.info("lineage_recorded", job_id=job_id, nodes=len(chain))

    async def get_lineage(self, tenant_id: str, source_id: str) -> dict:
        """Return full lineage graph for a source."""
        edges = await LineageEdge.find(
            LineageEdge.tenant_id == tenant_id
        ).to_list()

        node_ids = set()
        for e in edges:
            node_ids.add(e.from_node_id)
            node_ids.add(e.to_node_id)

        nodes = await LineageNode.find(
            {"node_id": {"$in": list(node_ids)}, "tenant_id": tenant_id}
        ).to_list()

        return {
            "nodes": [
                {"id": n.node_id, "type": n.node_type, "name": n.name, "service": n.service}
                for n in nodes
            ],
            "edges": [
                {"from": e.from_node_id, "to": e.to_node_id, "job_id": e.job_id}
                for e in edges
            ],
        }
