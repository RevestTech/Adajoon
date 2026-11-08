"""Test channel endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Channel, Country


@pytest.mark.unit
async def test_get_channels_empty(client: AsyncClient):
    """Test getting channels when database is empty."""
    response = await client.get("/api/channels")
    assert response.status_code == 200
    data = response.json()
    # GET /api/channels returns a PaginatedChannels envelope, not a bare list
    assert isinstance(data["channels"], list)
    assert len(data["channels"]) == 0
    assert data["total"] == 0


@pytest.mark.unit
async def test_get_channels_with_data(client: AsyncClient, test_db: AsyncSession):
    """Test getting channels with sample data."""
    # country_code has a real FK to countries.code - seed it first
    test_db.add(Country(code="US", name="United States"))
    await test_db.commit()

    # Create sample channel
    channel = Channel(
        id="test-channel-1",
        name="Test Channel",
        stream_url="https://example.com/stream.m3u8",
        logo="https://example.com/logo.png",
        country_code="US",
        categories="News",
        health_status="verified",
    )
    test_db.add(channel)
    await test_db.commit()

    response = await client.get("/api/channels")
    assert response.status_code == 200
    data = response.json()
    assert len(data["channels"]) == 1
    assert data["channels"][0]["id"] == "test-channel-1"
    assert data["channels"][0]["name"] == "Test Channel"


@pytest.mark.unit
async def test_get_categories(client: AsyncClient, test_db: AsyncSession):
    """Test getting categories."""
    # channel_count is computed from live Channel rows (get_categories_with_counts),
    # not a stored column on Category - don't pass it to the constructor.
    category = Category(id="news", name="News")
    test_db.add(category)
    await test_db.commit()

    response = await client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(cat["id"] == "news" for cat in data)


@pytest.mark.unit
async def test_search_channels(client: AsyncClient, test_db: AsyncSession):
    """Test channel search functionality."""
    # country_code has a real FK to countries.code - seed it first
    test_db.add(Country(code="US", name="United States"))
    test_db.add(Country(code="GB", name="United Kingdom"))
    await test_db.commit()

    # Create sample channels
    channels = [
        Channel(
            id="cnn",
            name="CNN International",
            country_code="US",
            categories="News",
            health_status="verified",
        ),
        Channel(
            id="bbc",
            name="BBC World News",
            country_code="GB",
            categories="News",
            health_status="verified",
        ),
        Channel(
            id="espn",
            name="ESPN",
            country_code="US",
            categories="Sports",
            health_status="online",
        ),
    ]
    for ch in channels:
        test_db.add(ch)
    await test_db.commit()

    # Search by query (the query param is named "query", not "q")
    response = await client.get("/api/channels?query=CNN")
    assert response.status_code == 200
    data = response.json()
    assert len(data["channels"]) >= 1
    assert any(ch["name"] == "CNN International" for ch in data["channels"])

    # Filter by category
    response = await client.get("/api/channels?category=Sports")
    assert response.status_code == 200
    data = response.json()
    assert len(data["channels"]) >= 1
    assert all(
        ch["categories"] and "Sports" in ch["categories"] for ch in data["channels"]
    )
