"""Test that rate limiting is actually enforced, not just configured.

SlowAPIMiddleware is what applies limiter.py's default_limits to every
route lacking its own @limiter.limit(...) - app.state.limiter and the
RateLimitExceeded exception handler alone do nothing without it.
"""

import pytest
import redis.asyncio as redis
from httpx import AsyncClient
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.main import app


@pytest.fixture(autouse=True)
async def _reset_rate_limits():
    client = redis.from_url(settings.redis_url)
    try:
        async for key in client.scan_iter(match="LIMITS:LIMITER*"):
            await client.delete(key)
    finally:
        await client.aclose()


@pytest.mark.unit
def test_slowapi_middleware_is_registered():
    """Regression guard for the global-default-limit-never-applied bug:
    app.state.limiter/the exception handler being set is not enough."""
    assert any(
        m.cls is SlowAPIMiddleware for m in app.user_middleware
    ), "SlowAPIMiddleware must be registered for default_limits to apply"


@pytest.mark.unit
async def test_passkey_login_options_is_rate_limited(client: AsyncClient):
    """passkey/login-options previously had no @limiter.limit at all,
    unlike every other login-adjacent endpoint (10/minute)."""
    statuses = []
    for _ in range(11):
        response = await client.post("/api/auth/passkey/login-options")
        statuses.append(response.status_code)
    assert 429 in statuses, "expected the 10/minute limit to trip within 11 requests"
