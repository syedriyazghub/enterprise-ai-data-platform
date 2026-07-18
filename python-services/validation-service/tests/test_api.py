"""Integration tests for validation API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_validate_endpoint_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/validation/validate", json={
            "records": [
                {"email": "alice@example.com", "age": "25"},
                {"email": "invalid-email",     "age": "30"},
            ],
            "rules": [
                {"field": "email", "rule_type": "email"},
                {"field": "age",   "rule_type": "numeric_range", "params": {"min": 0, "max": 120}},
            ],
            "detect_duplicates": True,
            "detect_schema": True,
        })
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 2
    assert data["total_errors"] == 1
    assert data["schema_profile"] is not None


@pytest.mark.asyncio
async def test_validate_endpoint_all_pass():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/validation/validate", json={
            "records": [{"pan": "ABCDE1234F"}, {"pan": "XYZPQ9876G"}],
            "rules": [{"field": "pan", "rule_type": "pan"}],
        })
    assert response.status_code == 200
    data = response.json()
    assert data["total_errors"] == 0
    assert data["passed_records"] == 2


@pytest.mark.asyncio
async def test_list_rules_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/validation/rules")
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    rule_types = [r["type"] for r in data["rules"]]
    assert "email" in rule_types
    assert "pan" in rule_types
    assert "gst" in rule_types


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
