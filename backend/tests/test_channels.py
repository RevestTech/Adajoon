"""Test channel endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Channel, Category


@pytest.mark.unit
async def test_get_channels_empty(client: AsyncClient):
    """Test getting channels when database is empty."""
    response = await client.get("/api/channels")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.unit
async def test_get_channels_with_data(client: AsyncClient, test_db: AsyncSession):
    """Test getting channels with sample data."""
    # Create sample channel
    channel = Channel(
        id="test-channel-1",
        name="Test Channel",
        stream_url="https://example.com/stream.m3u8",
        logo="https://example.com/logo.png",
        country="US",
        categories="News",
        health_status="verified",
    )
    test_db.add(channel)
    await test_db.commit()
    
    response = await client.get("/api/channels")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "test-channel-1"
    assert data[0]["name"] == "Test Channel"


@pytest.mark.unit
async def test_get_categories(client: AsyncClient, test_db: AsyncSession):
    """Test getting categories."""
    # Create sample category
    category = Category(id="news", name="News", channel_count=5)
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
    # Create sample channels
    channels = [
        Channel(id="cnn", name="CNN International", country="US", categories="News", health_status="verified"),
        Channel(id="bbc", name="BBC World News", country="GB", categories="News", health_status="verified"),
        Channel(id="espn", name="ESPN", country="US", categories="Sports", health_status="online"),
    ]
    for ch in channels:
        test_db.add(ch)
    await test_db.commit()
    
    # Search by query
    response = await client.get("/api/channels?q=CNN")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(ch["name"] == "CNN International" for ch in data)
    
    # Filter by category
    response = await client.get("/api/channels?category=Sports")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(ch["categories"] and "Sports" in ch["categories"] for ch in data)
