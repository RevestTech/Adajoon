import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, Base, async_session, get_db
from app.config import settings
from app.logging_config import setup_logging, RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import channels, categories, healthcheck, radio, auth, sitemap, history, languages, csrf, recommendations, playlists, parental, subscriptions, redis_health  # whitelabel
from app.services.iptv_service import full_sync
from app.services.radio_service import sync_radio_stations

# Prometheus metrics
try:
    from prometheus_fastapi_instrumentator import Instrumentator, metrics
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus-fastapi-instrumentator not installed, metrics disabled")

# Setup structured logging
log_level = os.getenv("LOG_LEVEL", "INFO")
json_logs = os.getenv("JSON_LOGS", "true").lower() in ("true", "1", "yes")
setup_logging(log_level=log_level, json_logs=json_logs)

logger = logging.getLogger(__name__)

# Rate limiting with Redis storage for distributed limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=settings.redis_url
)

# Migrations moved to Alembic. Run `alembic upgrade head` to apply.
# Legacy migrations kept for backwards compatibility during transition.
_MIGRATIONS = []

SYNC_API_KEY = os.getenv("SYNC_API_KEY", "")


async def initial_sync():
    """Run initial data sync after startup (only if ENABLE_INITIAL_SYNC is set)."""
    if not os.getenv("ENABLE_INITIAL_SYNC", "1") == "1":
        logger.info("Initial sync disabled via ENABLE_INITIAL_SYNC=0")
        return
    await asyncio.sleep(2)
    async with async_session() as db:
        try:
            await full_sync(db)
        except Exception as e:
            logger.error("IPTV sync failed: %s", e)
    async with async_session() as db:
        try:
            await sync_radio_stations(db)
        except Exception as e:
            logger.error("Radio sync failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        for sql in _MIGRATIONS:
            try:
                await conn.execute(text(sql))
            except Exception:
                pass
    logger.info("Database tables created")

    sync_task = asyncio.create_task(initial_sync())
    yield
    sync_task.cancel()
    await engine.dispose()


app = FastAPI(
    title="Adajoon",
    description="Online TV Channel Browser & Search",
    version="2.2.0",
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Add security headers for OAuth compatibility
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(channels.router)
app.include_router(categories.router)
app.include_router(healthcheck.router)
app.include_router(healthcheck.validator_router)
app.include_router(radio.router)
app.include_router(auth.router)
app.include_router(csrf.router)
app.include_router(history.router)
app.include_router(languages.router)
app.include_router(recommendations.router)
app.include_router(playlists.router)
app.include_router(parental.router)
app.include_router(subscriptions.router)
# app.include_router(whitelabel.router)  # TODO: Implement Tenant model first
app.include_router(redis_health.router)
app.include_router(sitemap.router)

# Setup Prometheus metrics
if PROMETHEUS_AVAILABLE:
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=False,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )
    
    # Add default metrics
    instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    
    logger.info("Prometheus metrics enabled at /metrics")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive readiness check.
    Tests all critical dependencies and queries.
    """
    import time
    from datetime import datetime
    from app.redis_client import health_check as redis_health_check
    from app.services.channel_service import get_categories_with_counts
    
    checks = {}
    start = time.time()
    overall_status = "healthy"
    
    # 1. Database connectivity
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)}
        overall_status = "unhealthy"
    
    # 2. Redis connectivity (optional - degraded if unavailable)
    try:
        redis_ok = await redis_health_check()
        checks["redis"] = {"status": "ok" if redis_ok else "degraded"}
        if not redis_ok:
            overall_status = "degraded" if overall_status == "healthy" else overall_status
    except Exception as e:
        checks["redis"] = {"status": "degraded", "message": str(e)}
        overall_status = "degraded" if overall_status == "healthy" else overall_status
    
    # 3. Critical query test (categories - the one that failed previously)
    try:
        query_start = time.time()
        rows = await get_categories_with_counts(db)
        query_time_ms = (time.time() - query_start) * 1000
        
        if query_time_ms > 5000:  # Warn if > 5 seconds
            checks["categories_query"] = {
                "status": "slow",
                "rows": len(rows),
                "time_ms": round(query_time_ms, 2)
            }
            overall_status = "degraded" if overall_status == "healthy" else overall_status
        else:
            checks["categories_query"] = {
                "status": "ok",
                "rows": len(rows),
                "time_ms": round(query_time_ms, 2)
            }
    except Exception as e:
        checks["categories_query"] = {"status": "error", "message": str(e)}
        overall_status = "unhealthy"
    
    total_time_ms = (time.time() - start) * 1000
    
    return {
        "status": overall_status,
        "checks": checks,
        "total_time_ms": round(total_time_ms, 2),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/sync")
async def trigger_sync(x_sync_key: str | None = Header(default=None, alias="X-Sync-Key")):
    """Manually trigger a data sync (requires SYNC_API_KEY header)."""
    if not SYNC_API_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Sync endpoint is disabled (SYNC_API_KEY not configured)")
    
    # Constant-time comparison to prevent timing attacks
    import secrets
    if not x_sync_key or not secrets.compare_digest(x_sync_key, SYNC_API_KEY):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing X-Sync-Key header")
    
    async with async_session() as db:
        results = await full_sync(db)
    return {"status": "complete", "results": results}
