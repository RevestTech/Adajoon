"""XMLTV EPG ingest from iptv-org/epg country guide packs."""

from __future__ import annotations

import gzip
import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import delete, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EpgProgramme

logger = logging.getLogger(__name__)

# Documented iptv-org guide layout (GitHub Pages). Override with EPG_BASE_URL if mirrored.
DEFAULT_EPG_BASE_URL = "https://iptv-org.github.io/epg/guides"
DEFAULT_COUNTRY_CODES = "us,uk,de"
DEFAULT_PRUNE_DAYS = 2

# Primary site per country from historical iptv-org GUIDES.md listings.
DEFAULT_COUNTRY_SITES: dict[str, list[str]] = {
    "us": ["tvtv.us"],
    "uk": ["sky.com"],
    "de": ["horizon.tv"],
}

UPSERT_BATCH_SIZE = 500


def get_country_codes() -> list[str]:
    raw = os.getenv("EPG_COUNTRY_CODES", DEFAULT_COUNTRY_CODES)
    return [c.strip().lower() for c in raw.split(",") if c.strip()]


def get_prune_days() -> int:
    raw = os.getenv("EPG_PRUNE_DAYS", str(DEFAULT_PRUNE_DAYS))
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_PRUNE_DAYS


def get_epg_base_url() -> str:
    return os.getenv("EPG_BASE_URL", DEFAULT_EPG_BASE_URL).rstrip("/")


def guide_urls_for_country(country_code: str) -> list[str]:
    """Build guide URLs for a country pack (site.epg.xml under country folder)."""
    cc = country_code.lower()
    base = get_epg_base_url()
    sites = DEFAULT_COUNTRY_SITES.get(cc, [f"{cc}"])
    urls: list[str] = []
    for site in sites:
        urls.append(f"{base}/{cc}/{site}.epg.xml")
        urls.append(f"{base}/{cc}/{site}.epg.xml.gz")
    return urls


def parse_xmltv_datetime(value: str) -> datetime | None:
    """Parse XMLTV timestamp like ``20240101120000 +0000`` or ``20240101120000``."""
    if not value:
        return None
    parts = value.strip().split()
    stamp = parts[0]
    if len(stamp) < 14:
        return None
    try:
        dt = datetime(
            int(stamp[0:4]),
            int(stamp[4:6]),
            int(stamp[6:8]),
            int(stamp[8:10]),
            int(stamp[10:12]),
            int(stamp[12:14]),
        )
    except ValueError:
        return None

    if len(parts) >= 2:
        tz = parts[1]
        if tz in ("UTC", "GMT", "Z"):
            return dt.replace(tzinfo=timezone.utc)
        # +HHMM / -HHMM
        if len(tz) == 5 and tz[0] in "+-" and tz[1:].isdigit():
            sign = 1 if tz[0] == "+" else -1
            hours = int(tz[1:3])
            minutes = int(tz[3:5])
            offset = timezone(sign * timedelta(hours=hours, minutes=minutes))
            return dt.replace(tzinfo=offset)
        try:
            return dt.replace(tzinfo=ZoneInfo(tz))
        except Exception:
            return dt.replace(tzinfo=timezone.utc)
    return dt.replace(tzinfo=timezone.utc)


def _first_text(parent: ET.Element, tag: str) -> str:
    el = parent.find(tag)
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _all_category_text(parent: ET.Element) -> str:
    cats = [
        (el.text or "").strip()
        for el in parent.findall("category")
        if el.text and el.text.strip()
    ]
    return ",".join(cats)


def parse_xmltv_programmes(xml_bytes: bytes) -> list[dict[str, Any]]:
    """Parse XMLTV ``<programme>`` elements into upsert-ready dicts."""
    root = ET.fromstring(xml_bytes)
    programmes: list[dict[str, Any]] = []
    for prog in root.findall("programme"):
        channel_id = (prog.get("channel") or "").strip()
        start_at = parse_xmltv_datetime(prog.get("start") or "")
        stop_at = parse_xmltv_datetime(prog.get("stop") or "")
        if not channel_id or start_at is None or stop_at is None:
            continue
        title = _first_text(prog, "title") or ""
        programmes.append(
            {
                "channel_id": channel_id,
                "start_at": start_at,
                "stop_at": stop_at,
                "title": title[:500],
                "subtitle": _first_text(prog, "sub-title")[:500],
                "description": _first_text(prog, "desc"),
                "category": _all_category_text(prog)[:255],
            }
        )
    return programmes


def decompress_if_gzip(data: bytes) -> bytes:
    if len(data) >= 2 and data[0] == 0x1F and data[1] == 0x8B:
        return gzip.decompress(data)
    return data


async def fetch_guide_xml(url: str, client: httpx.AsyncClient) -> bytes:
    resp = await client.get(url)
    resp.raise_for_status()
    return decompress_if_gzip(resp.content)


async def upsert_programmes(db: AsyncSession, programmes: list[dict[str, Any]]) -> int:
    """Idempotent upsert keyed by (channel_id, start_at). Returns rows touched."""
    if not programmes:
        return 0
    count = 0
    for i in range(0, len(programmes), UPSERT_BATCH_SIZE):
        chunk = programmes[i : i + UPSERT_BATCH_SIZE]
        stmt = pg_insert(EpgProgramme).values(chunk)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_epg_channel_start",
            set_={
                "stop_at": stmt.excluded.stop_at,
                "title": stmt.excluded.title,
                "subtitle": stmt.excluded.subtitle,
                "description": stmt.excluded.description,
                "category": stmt.excluded.category,
            },
        )
        await db.execute(stmt)
        count += len(chunk)
    await db.commit()
    return count


async def prune_old_programmes(db: AsyncSession, older_than_days: int | None = None) -> int:
    days = older_than_days if older_than_days is not None else get_prune_days()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        delete(EpgProgramme).where(EpgProgramme.stop_at < cutoff)
    )
    await db.commit()
    return int(result.rowcount or 0)


async def sync_country_pack(
    db: AsyncSession,
    country_code: str,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Fetch and upsert one country pack. Never raises — errors go in the result dict."""
    cc = country_code.lower()
    result: dict[str, Any] = {"upserted": 0, "error": None, "url": None}
    urls = guide_urls_for_country(cc)
    own_client = client is None
    http = client or httpx.AsyncClient(
        timeout=120,
        headers={"User-Agent": "Adajoon/1.0 EPG"},
        follow_redirects=True,
    )
    try:
        last_error: str | None = None
        for url in urls:
            try:
                xml_bytes = await fetch_guide_xml(url, http)
                programmes = parse_xmltv_programmes(xml_bytes)
                upserted = await upsert_programmes(db, programmes)
                result["upserted"] = upserted
                result["url"] = url
                result["error"] = None
                logger.info(
                    "EPG country=%s url=%s programmes=%d",
                    cc,
                    url,
                    upserted,
                )
                return result
            except Exception as e:
                last_error = str(e)
                logger.warning("EPG fetch failed country=%s url=%s: %s", cc, url, e)
                continue
        result["error"] = last_error or "No guide URLs configured"
        return result
    except Exception as e:
        result["error"] = str(e)
        logger.exception("EPG country pack failed country=%s: %s", cc, e)
        return result
    finally:
        if own_client:
            await http.aclose()


async def sync_epg(db: AsyncSession) -> dict[str, Any]:
    """Sync configured country packs. Failed packs do not abort the whole sync."""
    countries = get_country_codes()
    summary: dict[str, Any] = {
        "countries": {},
        "pruned": 0,
        "errors": [],
    }
    async with httpx.AsyncClient(
        timeout=120,
        headers={"User-Agent": "Adajoon/1.0 EPG"},
        follow_redirects=True,
    ) as client:
        for cc in countries:
            pack = await sync_country_pack(db, cc, client=client)
            summary["countries"][cc] = pack
            if pack.get("error"):
                summary["errors"].append({"country": cc, "error": pack["error"]})

    try:
        summary["pruned"] = await prune_old_programmes(db)
    except Exception as e:
        logger.exception("EPG prune failed: %s", e)
        summary["errors"].append({"country": "_prune", "error": str(e)})

    logger.info("EPG sync complete: %s", summary)
    return summary


# --- Query helpers (API) -----------------------------------------------------

SCHEDULE_DEFAULT_HOURS = 24
ON_NOW_DEFAULT_LIMIT = 50


def resolve_schedule_window(
    from_dt: datetime | None,
    to_dt: datetime | None,
    *,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Default schedule window: now → now+24h when from/to omitted."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    start = from_dt or current
    end = to_dt or (current + timedelta(hours=SCHEDULE_DEFAULT_HOURS))
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if end <= start:
        raise ValueError("to must be after from")
    return start, end


def overlaps_window(
    start_at: datetime,
    stop_at: datetime,
    window_from: datetime,
    window_to: datetime,
) -> bool:
    """True if programme interval overlaps [window_from, window_to)."""
    return start_at < window_to and stop_at > window_from


def is_airing_at(start_at: datetime, stop_at: datetime, at: datetime) -> bool:
    """True if programme is on air at `at` (start <= at < stop)."""
    return start_at <= at < stop_at


def matches_on_now_text(
    title: str,
    category: str,
    *,
    q: str | None = None,
    category_filter: str | None = None,
) -> bool:
    """Case-insensitive substring match for on-now search (mirrors ILIKE)."""
    if q:
        needle = q.strip().lower()
        if not needle:
            return False
        hay = f"{title or ''} {category or ''}".lower()
        if needle not in hay:
            return False
    if category_filter:
        needle = category_filter.strip().lower()
        if not needle:
            return False
        if needle not in (category or "").lower():
            return False
    return bool(q or category_filter)


async def get_channel_schedule(
    db: AsyncSession,
    channel_id: str,
    from_dt: datetime,
    to_dt: datetime,
) -> list[EpgProgramme]:
    """Programmes for a channel overlapping [from_dt, to_dt)."""
    stmt = (
        select(EpgProgramme)
        .where(
            EpgProgramme.channel_id == channel_id,
            EpgProgramme.start_at < to_dt,
            EpgProgramme.stop_at > from_dt,
        )
        .order_by(EpgProgramme.start_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_now_next(
    db: AsyncSession,
    channel_id: str,
    *,
    at: datetime | None = None,
) -> tuple[EpgProgramme | None, EpgProgramme | None]:
    """Current programme (if any) and the next one after it for a channel."""
    current_time = at or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    now_stmt = (
        select(EpgProgramme)
        .where(
            EpgProgramme.channel_id == channel_id,
            EpgProgramme.start_at <= current_time,
            EpgProgramme.stop_at > current_time,
        )
        .order_by(EpgProgramme.start_at.desc())
        .limit(1)
    )
    now_result = await db.execute(now_stmt)
    current = now_result.scalar_one_or_none()

    next_after = current.stop_at if current is not None else current_time
    next_stmt = (
        select(EpgProgramme)
        .where(
            EpgProgramme.channel_id == channel_id,
            EpgProgramme.start_at >= next_after,
        )
        .order_by(EpgProgramme.start_at)
        .limit(1)
    )
    next_result = await db.execute(next_stmt)
    nxt = next_result.scalar_one_or_none()
    return current, nxt


async def search_on_now(
    db: AsyncSession,
    *,
    q: str | None = None,
    category: str | None = None,
    at: datetime | None = None,
    limit: int = ON_NOW_DEFAULT_LIMIT,
) -> list[EpgProgramme]:
    """Programmes airing now whose title/category match q and/or category."""
    if not q and not category:
        raise ValueError("q or category required")

    current_time = at or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    clauses = [
        EpgProgramme.start_at <= current_time,
        EpgProgramme.stop_at > current_time,
    ]
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        clauses.append(
            or_(
                EpgProgramme.title.ilike(pattern),
                EpgProgramme.category.ilike(pattern),
            )
        )
    if category and category.strip():
        clauses.append(EpgProgramme.category.ilike(f"%{category.strip()}%"))

    stmt = (
        select(EpgProgramme)
        .where(*clauses)
        .order_by(EpgProgramme.channel_id, EpgProgramme.start_at)
        .limit(max(1, min(limit, 200)))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
