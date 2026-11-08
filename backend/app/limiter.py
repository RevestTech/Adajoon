"""Shared rate limiter, backed by Redis so limits apply correctly across
multiple backend instances. Every router needing @limiter.limit(...) should
import this instance rather than creating its own - a router-local
Limiter() with no storage_uri silently falls back to in-process memory,
which undercounts (and effectively multiplies) limits once this app runs
as more than one instance.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=settings.redis_url,
)
