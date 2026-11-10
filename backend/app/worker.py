import asyncio
import json
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import text

from app.database import Base, async_session, engine
from app.services.epg_service import sync_epg
from app.services.iptv_service import full_sync
from app.services.radio_service import sync_radio_stations
from app.services.settings_service import set_setting
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


_PHASE_FAILED = object()


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
        return _PHASE_FAILED


async def _record_phase_status(name: str, phase_ok: bool) -> None:
    """Persists one phase's last-run time/success into app_settings (a
    fresh session, independent of the phase's own - safe even if that
    phase's session is in a failed-transaction state). Admin -> Overview
    reads this back per-phase, not just the cycle-level aggregate, so a
    silently-failing phase (e.g. the iptv_full_sync deadlock seen in prod
    this week) is visible without reading Railway logs directly."""
    try:
        async with async_session() as status_db:
            await set_setting(
                status_db,
                f"sync_phase:{name}",
                json.dumps(
                    {
                        "last_run": datetime.now(timezone.utc).isoformat(),
                        "ok": phase_ok,
                    }
                ),
            )
    except Exception as e:
        logger.warning("Failed to record phase status for %s: %s", name, e)


async def run_cycle() -> bool:
    """Runs every sync phase. Returns True only if every phase succeeded, so
    callers can tell a real sync from one where every phase quietly failed."""
    ok = True

    async with async_session() as db:
        phase_ok = (
            await _phase("validate_all_channels", validate_all_channels(db))
            is not _PHASE_FAILED
        )
    await _record_phase_status("validate_all_channels", phase_ok)
    ok = ok and phase_ok

    async with async_session() as db:
        phase_ok = (
            await _phase("validate_all_radio", validate_all_radio(db))
            is not _PHASE_FAILED
        )
    await _record_phase_status("validate_all_radio", phase_ok)
    ok = ok and phase_ok

    async with async_session() as db:
        phase_ok = await _phase("iptv_full_sync", full_sync(db)) is not _PHASE_FAILED
    await _record_phase_status("iptv_full_sync", phase_ok)
    ok = ok and phase_ok

    async with async_session() as db:
        phase_ok = (
            await _phase("sync_radio_stations", sync_radio_stations(db))
            is not _PHASE_FAILED
        )
    await _record_phase_status("sync_radio_stations", phase_ok)
    ok = ok and phase_ok

    async with async_session() as db:
        phase_ok = await _phase("sync_epg", sync_epg(db)) is not _PHASE_FAILED
    await _record_phase_status("sync_epg", phase_ok)
    ok = ok and phase_ok

    return ok


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
        cycle_ok = False
        try:
            cycle_ok = await run_cycle()
        except Exception as e:
            logger.exception("Cycle error (continuing): %s", e)

        cycle_elapsed = time.monotonic() - cycle_t0
        logger.info(
            "=== Cycle finished in %.1fs; sleeping %ds ===",
            cycle_elapsed,
            SLEEP_SECONDS,
        )
        if cycle_ok:
            try:
                async with async_session() as db:
                    await set_setting(
                        db, "last_sync_at", datetime.now(timezone.utc).isoformat()
                    )
            except Exception as e:
                logger.warning("Failed to record last_sync_at: %s", e)
        else:
            logger.warning("Skipping last_sync_at update: cycle had phase failures")
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
