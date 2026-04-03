"""
Redis client for caching and distributed operations.

This module provides a singleton Redis client that:
- Caches API responses (categories, countries, stats)
- Stores rate limiting data (distributed across containers)
- Handles session management
- Tracks real-time metrics

Performance: ~2ms per operation vs ~200ms for PostgreSQL queries
"""
import json
import logging
from typing import Any, Optional
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)

# Global Redis client (initialized on first use)
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    """
    Get or create the Redis client singleton.
    
    This ensures we reuse the same connection pool across requests.
    Returns None if connection fails (graceful degradation).
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,  # Auto-decode bytes to strings
                socket_connect_timeout=2,  # Reduced from 5s
                socket_timeout=2,  # Add socket timeout
                socket_keepalive=True,
            )
            # Test connection
            await _redis_client.ping()
            logger.info(f"Redis connected: {settings.redis_url}")
        except Exception as e:
            logger.warning(f"Redis connection failed, continuing without cache: {e}")
            # Don't raise - just return None for graceful degradation
            _redis_client = None
    
    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    """
    Get cached value from Redis.
    
    Args:
        key: Cache key (e.g., "categories", "user:123")
    
    Returns:
        Parsed JSON value or None if not found
    
    Example:
        data = await cache_get("categories")
        if data:
            return data  # 2ms response!
    """
    try:
        client = await get_redis()
        if client is None:
            return None  # Redis unavailable
        value = await client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Redis cache_get error for key '{key}': {e}")
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Set cached value in Redis with automatic expiry.
    
    Args:
        key: Cache key
        value: Data to cache (will be JSON serialized)
        ttl: Time to live in seconds (default: 5 minutes)
    
    Returns:
        True if successful, False otherwise
    
    Example:
        await cache_set("categories", data, ttl=300)  # Cache for 5 minutes
    """
    try:
        client = await get_redis()
        if client is None:
            return False  # Redis unavailable
        await client.setex(
            key,
            ttl,
            json.dumps(value, default=str)  # default=str handles datetime, etc.
        )
        return True
    except Exception as e:
        logger.warning(f"Redis cache_set error for key '{key}': {e}")
        return False


async def cache_delete(key: str) -> bool:
    """
    Delete a cached value.
    
    Args:
        key: Cache key to delete
    
    Returns:
        True if deleted, False otherwise
    
    Example:
        await cache_delete("categories")  # Force re-fetch from DB
    """
    try:
        client = await get_redis()
        if client is None:
            return False  # Redis unavailable
        await client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Redis cache_delete error for key '{key}': {e}")
        return False


async def increment_counter(key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
    """
    Atomically increment a counter.
    
    Args:
        key: Counter key (e.g., "views:channel:abc")
        amount: Amount to increment by (default: 1)
        ttl: Optional expiry in seconds
    
    Returns:
        New counter value
    
    Example:
        views = await increment_counter("views:channel:abc")
        # views = 1, 2, 3, ... (atomic, thread-safe)
    """
    try:
        client = await get_redis()
        if client is None:
            return 0  # Redis unavailable
        new_value = await client.incrby(key, amount)
        if ttl and new_value == amount:  # First increment, set TTL
            await client.expire(key, ttl)
        return new_value
    except Exception as e:
        logger.warning(f"Redis increment error for key '{key}': {e}")
        return 0


async def health_check() -> bool:
    """
    Check if Redis is healthy.
    
    Returns:
        True if Redis responds to PING, False otherwise
    """
    try:
        client = await get_redis()
        if client is None:
            return False  # Redis unavailable
        await client.ping()
        return True
    except Exception:
        return False
