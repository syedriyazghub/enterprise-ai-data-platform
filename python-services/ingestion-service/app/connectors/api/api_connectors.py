"""REST API, GraphQL, and Webhook connectors."""
from typing import AsyncIterator, Any
import httpx
import structlog

from app.connectors.base import BaseConnector, ConnectorConfig, IngestedRecord

logger = structlog.get_logger()


class RESTAPIConnector(BaseConnector):
    """Ingests data from REST APIs with pagination support."""

    async def connect(self) -> None:
        params = self.config.connection_params
        self._base_url = params["base_url"]
        self._headers = params.get("headers", {})
        self._auth = params.get("auth")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers,
            timeout=30.0,
        )

    async def disconnect(self) -> None:
        await self._client.aclose()

    async def test_connection(self) -> bool:
        try:
            resp = await self._client.get("/")
            return resp.status_code < 500
        except Exception:
            return False

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        params = self.config.connection_params
        endpoint = params.get("endpoint", "/")
        pagination = self.config.options.get("pagination", {})
        page_param = pagination.get("page_param", "page")
        page_size_param = pagination.get("page_size_param", "page_size")
        page_size = pagination.get("page_size", 100)
        data_key = params.get("data_key", "data")

        page = 1
        while True:
            query_params = {page_param: page, page_size_param: page_size}
            query_params.update(params.get("query_params", {}))

            response = await self._client.get(endpoint, params=query_params)
            response.raise_for_status()
            body = response.json()

            records = body.get(data_key, body) if isinstance(body, dict) else body
            if not records:
                break

            for record in records:
                yield IngestedRecord(
                    data=record if isinstance(record, dict) else {"value": record},
                    source_metadata={"source_type": "rest_api", "url": str(response.url)},
                )

            if len(records) < page_size:
                break
            page += 1


class GraphQLConnector(BaseConnector):
    """Ingests data from GraphQL APIs."""

    async def connect(self) -> None:
        params = self.config.connection_params
        self._endpoint = params["endpoint"]
        self._headers = params.get("headers", {"Content-Type": "application/json"})
        self._client = httpx.AsyncClient(headers=self._headers, timeout=30.0)

    async def disconnect(self) -> None:
        await self._client.aclose()

    async def test_connection(self) -> bool:
        try:
            resp = await self._client.post(
                self._endpoint,
                json={"query": "{ __typename }"},
            )
            return resp.status_code == 200
        except Exception:
            return False

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        params = self.config.connection_params
        query = params["query"]
        variables = params.get("variables", {})
        data_path = params.get("data_path", [])

        response = await self._client.post(
            self._endpoint,
            json={"query": query, "variables": variables},
        )
        response.raise_for_status()
        body = response.json()

        data: Any = body.get("data", {})
        for key in data_path:
            data = data.get(key, {})

        records = data if isinstance(data, list) else [data]
        for record in records:
            yield IngestedRecord(
                data=record,
                source_metadata={"source_type": "graphql", "endpoint": self._endpoint},
            )
