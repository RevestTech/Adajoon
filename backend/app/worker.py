import asyncio
import logging
import time
from textwrap import dedent

from sqlalchemy import text

from app.database import Base, async_session, engine
from app.services.epg_service import sync_epg
from app.services.iptv_service import full_sync
from app.services.radio_service import sync_radio_stations
from app.services.validator_service import validate_all_channels, validate_all_radio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app.worker")

SLEEP_SECONDS = 3600

MIGRATIONS = [
    "ALTER TABLE channels ADD COLUMN IF NOT EXISTS last_validated_at VARCHAR(50) DEFAULT '';",
    "ALTER TABLE radio_stations ADD COLUMN IF NOT EXISTS health_status VARCHAR(20) DEFAULT 'unknown';",
    "ALTER TABLE radio_stations ADD COLUMN IF NOT EXISTS health_checked_at VARCHAR(50) DEFAULT '';",
]


async def _phase(name: str, coro):
    t0 = time.monotonic()
    logger.info("Phase start: %s", name)
    try:
        result = await coro
        elapsed = time.monotonic() - t0
        logger.info("Phase complete: %s in %.1fs result=%s", name, elapsed, result)
        return result
    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.exception("Phase failed: %s after %.1fs: %s", name, elapsed, e)
        return None


async def run_cycle():
    async with async_session() as db:
        await _phase("validate_all_channels", validate_all_channels(db))

    async with async_session() as db:
        await _phase("validate_all_radio", validate_all_radio(db))

    async with async_session() as db:
        await _phase("iptv_full_sync", full_sync(db))

    async with async_session() as db:
        await _phase("sync_radio_stations", sync_radio_stations(db))

    async with async_session() as db:
        await _phase("sync_epg", sync_epg(db))


async def _run_migrations():
    """Add new columns to existing tables (idempotent)."""
    async with engine.begin() as conn:
        for sql in MIGRATIONS:
            try:
                await conn.execute(text(sql))
                logger.info("Migration OK: %s", sql.strip()[:80])
            except Exception as e:
                logger.warning("Migration skipped: %s — %s", sql.strip()[:80], e)


async def main():
    logger.info("Validator worker starting")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _run_migrations()
    logger.info("Database schema ensured")

    while True:
        cycle_t0 = time.monotonic()
        logger.info("=== Validation cycle started ===")
        try:
            await run_cycle()
        except Exception as e:
            logger.exception("Cycle error (continuing): %s", e)

        cycle_elapsed = time.monotonic() - cycle_t0
        logger.info(
            "=== Cycle finished in %.1fs; sleeping %ds ===",
            cycle_elapsed,
            SLEEP_SECONDS,
        )
        try:
            await asyncio.sleep(SLEEP_SECONDS)
        except asyncio.CancelledError:
            logger.info("Worker cancelled during sleep")
            raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
