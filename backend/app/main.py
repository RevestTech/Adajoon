import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, async_session
from app.routers import channels, categories
from app.services.iptv_service import full_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initial_sync():
    """Run initial data sync after startup."""
    await asyncio.sleep(2)
    async with async_session() as db:
        try:
            await full_sync(db)
        except Exception as e:
            logger.error("Initial sync failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    sync_task = asyncio.create_task(initial_sync())
    yield
    sync_task.cancel()
    await engine.dispose()


app = FastAPI(
    title="ReTV",
    description="Online TV Channel Browser & Search",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(channels.router)
app.include_router(categories.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/sync")
async def trigger_sync():
    """Manually trigger a data sync."""
    async with async_session() as db:
        results = await full_sync(db)
    return {"status": "complete", "results": results}
