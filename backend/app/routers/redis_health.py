"""Redis health check and cache management endpoints."""

from fastapi import APIRouter, Depends

from app.csrf import verify_csrf_token
from app.middleware.admin_required import require_admin
from app.models import User
from app.redis_client import cache_delete, health_check

router = APIRouter(prefix="/api/redis", tags=["redis"])


@router.get("/health")
async def redis_health():
    """
    Check if Redis is connected and responding.

    Returns:
        {"status": "healthy"} if Redis is up
        {"status": "unhealthy"} if Redis is down
    """
    is_healthy = await health_check()
    return {"status": "healthy" if is_healthy else "unhealthy", "connected": is_healthy}


@router.post("/cache/clear/{key}")
async def clear_cache(
    key: str,
    admin_user: User = Depends(require_admin),
    _csrf: None = Depends(verify_csrf_token),
):
    """
    Clear a specific cache key. Requires admin access.

    Useful for forcing fresh data after content updates.

    Args:
        key: Cache key to clear (e.g., "categories", "countries", "stats")

    Example:
        POST /api/redis/cache/clear/categories
        → Forces next request to fetch fresh data from DB
    """
    success = await cache_delete(key)
    return {
        "success": success,
        "message": (
            f"Cache key '{key}' cleared" if success else f"Failed to clear '{key}'"
        ),
    }
