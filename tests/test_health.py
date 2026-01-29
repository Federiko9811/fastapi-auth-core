"""
Tests for health check endpoints.
"""

from httpx import AsyncClient


async def test_root_endpoint(client: AsyncClient) -> None:
    """Test root endpoint returns OK status."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "project" in data


async def test_health_endpoint(client: AsyncClient) -> None:
    """Test health endpoint returns system status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data
