"""Test health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_health_endpoint(client: AsyncClient):
    """Test basic health endpoint returns 200."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.unit
async def test_health_ready_endpoint(client: AsyncClient):
    """Test readiness endpoint checks database connectivity.

    Overall status is "degraded" rather than "ok" when Redis is unreachable
    (there's no Redis service in this test environment, same as CI) - that's
    the endpoint correctly reporting an optional dependency being down, not a
    failure. The database and query checks must still be "ok" regardless.
    """
    response = await client.get("/api/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["categories_query"]["status"] == "ok"


@pytest.mark.unit
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint.

    `/` deliberately returns a bare {"status": "ok"} health-check body (see
    PR #19) to avoid a proxy loop with the frontend - it's not meant to carry
    API info/a message/title.
    """
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
