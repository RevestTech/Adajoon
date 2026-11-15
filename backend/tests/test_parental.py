"""Test parental controls / kids mode endpoints and enforcement."""

import pytest
import redis.asyncio as redis
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Channel, Country, RadioStation, User
from app.routers.auth import create_token


@pytest.fixture(autouse=True)
async def _reset_rate_limits():
    """The shared limiter is Redis-backed (see app/limiter.py) so its
    counters persist across tests in the same run, not just across requests
    within one test - without this, toggle_kids_mode's 10/minute limit trips
    partway through this file regardless of which test is "at fault"."""
    client = redis.from_url(settings.redis_url)
    try:
        async for key in client.scan_iter(match="LIMITS:LIMITER*"):
            await client.delete(key)
    finally:
        await client.aclose()


@pytest.fixture
async def test_user(test_db: AsyncSession):
    user = User(
        email="parent@example.com",
        name="Parent",
        provider="google",
        provider_id="google_parental_1",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    token = create_token(test_user.id, test_user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.unit
async def test_toggle_kids_mode_on_requires_no_pin(
    client: AsyncClient, auth_headers
):
    response = await client.post(
        "/api/parental/kids-mode", json={"enabled": True}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["kids_mode_enabled"] is True


@pytest.mark.unit
async def test_disable_kids_mode_requires_pin_when_pin_set(
    client: AsyncClient, auth_headers
):
    # Set a PIN and enable kids mode
    await client.post(
        "/api/parental/set-pin", json={"pin": "1234"}, headers=auth_headers
    )
    await client.post(
        "/api/parental/kids-mode", json={"enabled": True}, headers=auth_headers
    )

    # Disabling without a PIN is rejected
    response = await client.post(
        "/api/parental/kids-mode", json={"enabled": False}, headers=auth_headers
    )
    assert response.status_code == 400

    # Disabling with the wrong PIN is rejected
    response = await client.post(
        "/api/parental/kids-mode",
        json={"enabled": False, "pin": "9999"},
        headers=auth_headers,
    )
    assert response.status_code == 401

    # Disabling with the correct PIN succeeds
    response = await client.post(
        "/api/parental/kids-mode",
        json={"enabled": False, "pin": "1234"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["kids_mode_enabled"] is False


@pytest.mark.unit
async def test_disable_kids_mode_without_pin_set_needs_no_pin(
    client: AsyncClient, auth_headers
):
    """If kids mode was somehow enabled without ever setting a PIN, disabling
    stays unblocked - there'd be no way to turn it back off otherwise."""
    await client.post(
        "/api/parental/kids-mode", json={"enabled": True}, headers=auth_headers
    )
    response = await client.post(
        "/api/parental/kids-mode", json={"enabled": False}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["kids_mode_enabled"] is False


@pytest.mark.unit
async def test_kids_mode_filters_adult_radio_stations(
    client: AsyncClient, test_db: AsyncSession, auth_headers, test_user
):
    test_db.add_all(
        [
            RadioStation(id="pop-station", name="Pop FM", tags="pop,music"),
            RadioStation(id="adult-station", name="Late Night", tags="talk,adult content"),
        ]
    )
    await test_db.commit()

    # Not in kids mode: both stations visible
    response = await client.get("/api/radio/stations", headers=auth_headers)
    assert response.status_code == 200
    ids = {s["id"] for s in response.json()["stations"]}
    assert ids == {"pop-station", "adult-station"}

    # Enable kids mode
    await client.post(
        "/api/parental/kids-mode", json={"enabled": True}, headers=auth_headers
    )

    # Now the adult-tagged station is excluded from search...
    response = await client.get("/api/radio/stations", headers=auth_headers)
    assert response.status_code == 200
    ids = {s["id"] for s in response.json()["stations"]}
    assert ids == {"pop-station"}

    # ...and from direct station lookup by id.
    response = await client.get(
        "/api/radio/stations/adult-station", headers=auth_headers
    )
    assert response.status_code == 404

    response = await client.get(
        "/api/radio/stations/pop-station", headers=auth_headers
    )
    assert response.status_code == 200

    # Anonymous users (not kids-mode) still see everything.
    response = await client.get("/api/radio/stations")
    assert response.status_code == 200
    ids = {s["id"] for s in response.json()["stations"]}
    assert ids == {"pop-station", "adult-station"}


@pytest.mark.unit
async def test_nsfw_channel_not_reachable_by_direct_id(
    client: AsyncClient, test_db: AsyncSession
):
    test_db.add(Country(code="US", name="United States"))
    await test_db.commit()
    test_db.add(
        Channel(
            id="nsfw-channel",
            name="Adult Channel",
            is_nsfw=True,
            country_code="US",
            stream_url="https://example.com/stream.m3u8",
        )
    )
    await test_db.commit()

    response = await client.get("/api/channels/nsfw-channel")
    assert response.status_code == 404

    response = await client.get("/api/channels/nsfw-channel/streams")
    assert response.status_code == 200
    assert response.json() == []
