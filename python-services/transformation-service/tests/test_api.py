"""Integration tests for transformation service API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_transform_endpoint_basic():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/transform/transform", json={
            "records": [{"name": "  alice  ", "age": "25"}],
            "rules": [
                {"transformation_type": "trim",      "source_field": "name"},
                {"transformation_type": "uppercase", "source_field": "name"},
                {"transformation_type": "cast",      "source_field": "age", "params": {"type": "int"}},
            ],
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["records"][0]["name"] == "ALICE"
    assert data["records"][0]["age"] == 25
    assert data["rules_applied"] == 3
    assert data["records_out"] == 1


@pytest.mark.asyncio
async def test_transform_endpoint_mask_pii():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/transform/transform", json={
            "records": [{"email": "alice@example.com"}],
            "rules": [{"transformation_type": "mask_pii", "source_field": "email", "params": {"mask_type": "email"}}],
        })
    assert resp.status_code == 200
    masked = resp.json()["records"][0]["email"]
    assert "***@" in masked


@pytest.mark.asyncio
async def test_transform_endpoint_invalid_rule_type():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/transform/transform", json={
            "records": [{"field": "value"}],
            "rules": [{"transformation_type": "nonexistent_type", "source_field": "field"}],
        })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_transformations():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/transform/transformations")
    assert resp.status_code == 200
    data = resp.json()
    assert "transformations" in data
    assert len(data["transformations"]) >= 16


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_transform_empty_records_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/transform/transform", json={
            "records": [],
            "rules": [{"transformation_type": "trim", "source_field": "name"}],
        })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_transform_hash_produces_64_char_hex():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/transform/transform", json={
            "records": [{"ssn": "123-45-6789"}],
            "rules": [{"transformation_type": "hash", "source_field": "ssn"}],
        })
    assert resp.status_code == 200
    assert len(resp.json()["records"][0]["ssn"]) == 64
