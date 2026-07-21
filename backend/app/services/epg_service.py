"""EPG ingest (XMLTV) and schedule queries."""
from __future__ import annotations

import gzip
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Channel, EpgProgramme

logger = logging.getLogger(__name__)


def _normalize_channel_id(raw: str) -> str:
    cid = (raw or "").strip()
    if "@" in cid:
        cid = cid.split("@", 1)[0]
    return cid


def _parse_xmltv_time(value: str) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    # Formats: 20260402120000 +0000 | 20260402120000 +0000 | 20260402120000
    try:
        if " " in raw:
            dt_part, tz_part = raw.split(" ", 1)
            base = datetime.strptime(dt_part[:14], "%Y%m%d%H%M%S")
            tz_part = tz_part.strip()
            if tz_part.startswith(("+", "-")) and len(tz_part) >= 5:
                sign = 1 if tz_part[0] == "+" else -1
                hours = int(tz_part[1:3])
                mins = int(tz_part[3:5])
                offset = timezone(sign * timedelta(hours=hours, minutes=mins))
                return base.replace(tzinfo=offset).astimezone(timezone.utc)
            return base.replace(tzinfo=timezone.utc)
        base = datetime.strptime(raw[:14], "%Y%m%d%H%M%S")
        return base.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _text(el: ET.Element | None, default: str = "") -> str:
    if el is None or el.text is None:
        return default
    return el.text.strip()


async def _fetch_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Adajoon/1.0"})
        resp.raise_for_status()
        data = resp.content
    if url.endswith(".gz") or data[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(data)
        except OSError:
            return data
    return data


def parse_xmltv_programmes(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    programmes: list[dict] = []
    for prog in root.findall("programme"):
        channel_id = _normalize_channel_id(prog.get("channel", ""))
        if not channel_id:
            continue
        start_at = _parse_xmltv_time(prog.get("start", ""))
        stop_at = _parse_xmltv_time(prog.get("stop", ""))
        if not start_at or not stop_at:
            continue
        title = _text(prog.find("title"))
        subtitle = _text(prog.find("sub-title"))
        description = _text(prog.find("desc"))
        categories = [_text(c) for c in prog.findall("category") if _text(c)]
        programmes.append({
            "channel_id": channel_id,
            "start_at": start_at,
            "stop_at": stop_at,
            "title": title[:500],
            "subtitle": subtitle[:500],
            "description": description[:4000],
            "category": ";".join(categories)[:255],
        })
    return programmes


async def sync_epg(db: AsyncSession) -> dict:
    """Download configured XMLTV feeds and upsert programmes for known channels."""
    feeds = settings.epg_feeds
    if not feeds:
        logger.warning("No EPG feeds configured")
        return {"feeds": 0, "programmes": 0, "matched": 0}

    known = {
        row[0]
        for row in (await db.execute(select(Channel.id))).all()
    }

    total_parsed = 0
    total_matched = 0
    for url in feeds:
        try:
            xml_bytes = await _fetch_bytes(url)
            rows = parse_xmltv_programmes(xml_bytes)
            total_parsed += len(rows)
            matched = [r for r in rows if r["channel_id"] in known]
            total_matched += len(matched)
            if not matched:
                logger.info("EPG feed %s: %d programmes, 0 matched known channels", url, len(rows))
                continue

            channel_ids = {r["channel_id"] for r in matched}
            await db.execute(
                delete(EpgProgramme).where(EpgProgramme.channel_id.in_(channel_ids))
            )
            batch: list[EpgProgramme] = []
            for r in matched:
                batch.append(EpgProgramme(**r))
                if len(batch) >= 500:
                    db.add_all(batch)
                    await db.flush()
                    batch = []
            if batch:
                db.add_all(batch)
                await db.flush()
            await db.commit()
            logger.info(
                "EPG feed %s: parsed=%d matched=%d channels=%d",
                url, len(rows), len(matched), len(channel_ids),
            )
        except Exception as e:
            logger.error("EPG feed failed %s: %s", url, e, exc_info=True)
            await db.rollback()

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.epg_retain_days)
    try:
        await db.execute(delete(EpgProgramme).where(EpgProgramme.stop_at < cutoff))
        await db.commit()
    except Exception as e:
        logger.error("EPG prune failed: %s", e, exc_info=True)
        await db.rollback()

    return {"feeds": len(feeds), "programmes": total_parsed, "matched": total_matched}


def _programme_dict(p: EpgProgramme) -> dict:
    return {
        "id": p.id,
        "channel_id": p.channel_id,
        "start_at": p.start_at.isoformat() if p.start_at else "",
        "stop_at": p.stop_at.isoformat() if p.stop_at else "",
        "title": p.title or "",
        "subtitle": p.subtitle or "",
        "description": p.description or "",
        "category": p.category or "",
    }


async def get_channel_epg(
    db: AsyncSession,
    channel_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict]:
    now = datetime.now(timezone.utc)
    start = start or (now - timedelta(hours=1))
    end = end or (now + timedelta(hours=24))
    result = await db.execute(
        select(EpgProgramme)
        .where(
            EpgProgramme.channel_id == channel_id,
            EpgProgramme.stop_at >= start,
            EpgProgramme.start_at <= end,
        )
        .order_by(EpgProgramme.start_at)
        .limit(200)
    )
    return [_programme_dict(p) for p in result.scalars().all()]


async def get_now_next(db: AsyncSession, channel_id: str) -> dict:
    now = datetime.now(timezone.utc)
    current = (
        await db.execute(
            select(EpgProgramme)
            .where(
                EpgProgramme.channel_id == channel_id,
                EpgProgramme.start_at <= now,
                EpgProgramme.stop_at > now,
            )
            .order_by(EpgProgramme.start_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    nxt = (
        await db.execute(
            select(EpgProgramme)
            .where(
                EpgProgramme.channel_id == channel_id,
                EpgProgramme.start_at > now,
            )
            .order_by(EpgProgramme.start_at)
            .limit(1)
        )
    ).scalar_one_or_none()

    return {
        "channel_id": channel_id,
        "now": _programme_dict(current) if current else None,
        "next": _programme_dict(nxt) if nxt else None,
    }


async def search_on_now(
    db: AsyncSession,
    q: str | None = None,
    category: str | None = None,
    limit: int = 40,
) -> list[dict]:
    now = datetime.now(timezone.utc)
    query = (
        select(EpgProgramme, Channel)
        .join(Channel, Channel.id == EpgProgramme.channel_id)
        .where(
            EpgProgramme.start_at <= now,
            EpgProgramme.stop_at > now,
            Channel.is_nsfw == False,
        )
    )
    if category:
        query = query.where(EpgProgramme.category.ilike(f"%{category}%"))
    if q:
        pattern = f"%{q}%"
        query = query.where(
            or_(
                EpgProgramme.title.ilike(pattern),
                EpgProgramme.subtitle.ilike(pattern),
                EpgProgramme.description.ilike(pattern),
                EpgProgramme.category.ilike(pattern),
                Channel.name.ilike(pattern),
                Channel.categories.ilike(pattern),
            )
        )
    result = await db.execute(query.order_by(EpgProgramme.start_at).limit(limit))
    rows = result.all()
    out: list[dict] = []
    for prog, ch in rows:
        item = _programme_dict(prog)
        item["channel"] = {
            "id": ch.id,
            "name": ch.name,
            "logo": ch.logo or "",
            "categories": ch.categories or "",
            "country_code": ch.country_code or "",
            "stream_url": ch.stream_url or "",
            "health_status": ch.health_status or "unknown",
        }
        out.append(item)
    return out
