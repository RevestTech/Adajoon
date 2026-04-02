import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, Base, async_session, get_db
from app.config import settings
from app.routers import channels, categories, healthcheck, radio, auth
from app.services.iptv_service import full_sync
from app.services.radio_service import sync_radio_stations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_MIGRATIONS = [
    "ALTER TABLE channels ADD COLUMN IF NOT EXISTS last_validated_at VARCHAR(50) DEFAULT '';",
    "ALTER TABLE radio_stations ADD COLUMN IF NOT EXISTS health_status VARCHAR(20) DEFAULT 'unknown';",
    "ALTER TABLE radio_stations ADD COLUMN IF NOT EXISTS health_checked_at VARCHAR(50) DEFAULT '';",
    "CREATE INDEX IF NOT EXISTS ix_channels_health_status ON channels (health_status);",
    "CREATE INDEX IF NOT EXISTS ix_channels_health_checked_at ON channels (health_checked_at);",
    "CREATE INDEX IF NOT EXISTS ix_radio_health_status ON radio_stations (health_status);",
    "CREATE INDEX IF NOT EXISTS ix_radio_last_check_ok ON radio_stations (last_check_ok);",
    "CREATE INDEX IF NOT EXISTS ix_radio_health_checked_at ON radio_stations (health_checked_at);",
    """CREATE TABLE IF NOT EXISTS user_votes (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        item_type VARCHAR(10) NOT NULL,
        item_id VARCHAR(255) NOT NULL,
        vote_type VARCHAR(20) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT now()
    );""",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_user_vote_unique ON user_votes (user_id, item_type, item_id, vote_type);",
    "CREATE INDEX IF NOT EXISTS ix_vote_item ON user_votes (item_type, item_id);",
]

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
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=500)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(channels.router)
app.include_router(categories.router)
app.include_router(healthcheck.router)
app.include_router(healthcheck.validator_router)
app.include_router(radio.router)
app.include_router(auth.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    """Readiness probe — verifies DB connectivity."""
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.post("/api/sync")
async def trigger_sync():
    """Manually trigger a data sync (requires SYNC_API_KEY)."""
    if SYNC_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Use the worker for syncing")
    async with async_session() as db:
        results = await full_sync(db)
    return {"status": "complete", "results": results}
