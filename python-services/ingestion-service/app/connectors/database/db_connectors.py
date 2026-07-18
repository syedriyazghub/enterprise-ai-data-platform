"""Database connectors: PostgreSQL, MySQL, SQL Server, Oracle, MongoDB."""
from typing import AsyncIterator
import asyncpg
import structlog

from app.connectors.base import BaseConnector, ConnectorConfig, IngestedRecord

logger = structlog.get_logger()


class PostgreSQLConnector(BaseConnector):
    """Ingests data from PostgreSQL databases."""

    async def connect(self) -> None:
        params = self.config.connection_params
        self._pool = await asyncpg.create_pool(
            host=params["host"],
            port=params.get("port", 5432),
            database=params["database"],
            user=params["user"],
            password=params["password"],
            min_size=1,
            max_size=5,
        )

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()

    async def test_connection(self) -> bool:
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error("pg_connection_test_failed", error=str(e))
            return False

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        params = self.config.connection_params
        query = params.get("query") or f"SELECT * FROM {params['table']}"
        batch_size = self.config.options.get("batch_size", 1000)

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                cursor = await conn.cursor(query)
                while True:
                    rows = await cursor.fetch(batch_size)
                    if not rows:
                        break
                    for row in rows:
                        yield IngestedRecord(
                            data=dict(row),
                            source_metadata={"source_type": "postgresql", "query": query},
                        )


class MongoDBConnector(BaseConnector):
    """Ingests data from MongoDB collections."""

    async def connect(self) -> None:
        from motor.motor_asyncio import AsyncIOMotorClient
        params = self.config.connection_params
        self._client = AsyncIOMotorClient(params["uri"])
        self._db = self._client[params["database"]]
        self._collection = self._db[params["collection"]]

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()

    async def test_connection(self) -> bool:
        try:
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        filter_query = self.config.options.get("filter", {})
        batch_size = self.config.options.get("batch_size", 1000)

        async for doc in self._collection.find(filter_query).batch_size(batch_size):
            doc["_id"] = str(doc["_id"])
            yield IngestedRecord(
                data=doc,
                source_metadata={"source_type": "mongodb", "collection": self._collection.name},
            )
