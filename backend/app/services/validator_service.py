import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import httpx
import m3u8
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import Channel, RadioStation, Stream
from app.services.healthcheck_service import probe_stream

logger = logging.getLogger(__name__)

VALIDATE_TIMEOUT = 12.0
VALIDATE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
}

AUDIO_CT_PREFIXES = (
    "audio/",
    "application/ogg",
    "application/octet-stream",
    "video/ogg",
)
AUDIO_CT_EXACT = frozenset({"application/vnd.apple.mpegurl"})  # rare for raw radio


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=VALIDATE_TIMEOUT,
        follow_redirects=True,
        headers=VALIDATE_HEADERS,
        verify=False,
    )


def _ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)


def _geo_hint(status_code: int, body_sample: str) -> bool:
    if status_code != 403:
        return False
    low = body_sample.lower()
    hints = ("geo", "country", "region", "blocked", "forbidden", "not available", "denied")
    return any(h in low for h in hints)


def _segment_content_type_ok(ct: str) -> bool:
    ct = (ct or "").split(";")[0].strip().lower()
    if not ct:
        return True
    if ct.startswith("video/"):
        return True
    if ct == "application/octet-stream":
        return True
    if ct in ("application/mp4", "audio/mp4"):
        return True
    return False


async def deep_validate_hls(url: str) -> dict[str, Any]:
    """Fetch HLS manifest, parse with m3u8, attempt first media segment (Range 4KB)."""
    start = time.monotonic()
    base_result: dict[str, Any] = {
        "status": "offline",
        "detail": "",
        "response_time_ms": 0,
    }

    try:
        async with _client() as client:
            r = await client.get(url)
            base_result["response_time_ms"] = _ms(start)

            if r.status_code in (403, 451) and _geo_hint(r.status_code, r.text[:500]):
                base_result["status"] = "geo_blocked"
                base_result["detail"] = f"HTTP {r.status_code} (likely geo/restriction)"
                return base_result

            if r.status_code >= 400:
                base_result["status"] = "offline"
                base_result["detail"] = f"Manifest HTTP {r.status_code}"
                return base_result

            text = r.text
            if "#EXTM3U" not in text:
                base_result["status"] = "offline"
                base_result["detail"] = "Not an HLS manifest"
                return base_result

            manifest_url = str(r.url)
            playlist = m3u8.loads(text, uri=manifest_url)

            if playlist.is_variant and playlist.playlists:
                variant = playlist.playlists[0]
                sub_url = getattr(variant, "absolute_uri", None) or urljoin(
                    playlist.base_uri, variant.uri
                )
                sub_r = await client.get(sub_url)
                base_result["response_time_ms"] = _ms(start)
                if sub_r.status_code in (403, 451) and _geo_hint(sub_r.status_code, sub_r.text[:500]):
                    base_result["status"] = "geo_blocked"
                    base_result["detail"] = f"Variant manifest HTTP {sub_r.status_code}"
                    return base_result
                if sub_r.status_code >= 400:
                    base_result["status"] = "manifest_only"
                    base_result["detail"] = f"Variant manifest HTTP {sub_r.status_code}"
                    return base_result
                sub_text = sub_r.text
                if "#EXTM3U" not in sub_text:
                    base_result["status"] = "manifest_only"
                    base_result["detail"] = "Variant response is not HLS"
                    return base_result
                playlist = m3u8.loads(sub_text, uri=str(sub_r.url))

            seg_urls: list[str] = []
            for seg in playlist.segments[:2]:
                u = getattr(seg, "absolute_uri", None) or urljoin(playlist.base_uri, seg.uri)
                if u:
                    seg_urls.append(u)

            if not seg_urls:
                base_result["status"] = "manifest_only"
                base_result["detail"] = "No media segments in playlist"
                return base_result

            seg_url = seg_urls[0]
            seg_headers = {**VALIDATE_HEADERS, "Range": "bytes=0-4095"}
            seg_r = await client.get(seg_url, headers=seg_headers)
            base_result["response_time_ms"] = _ms(start)

            if seg_r.status_code in (403, 451) and _geo_hint(seg_r.status_code, seg_r.text[:300] if seg_r.text else ""):
                base_result["status"] = "geo_blocked"
                base_result["detail"] = f"Segment HTTP {seg_r.status_code}"
                return base_result

            if seg_r.status_code == 404:
                base_result["status"] = "manifest_only"
                base_result["detail"] = "First segment returned 404"
                return base_result

            if seg_r.status_code not in (200, 206):
                base_result["status"] = "manifest_only"
                base_result["detail"] = f"Segment HTTP {seg_r.status_code}"
                return base_result

            body = seg_r.content or b""
            if len(body) < 1:
                base_result["status"] = "manifest_only"
                base_result["detail"] = "Empty segment response"
                return base_result

            ct = seg_r.headers.get("content-type", "")
            if _segment_content_type_ok(ct):
                base_result["status"] = "verified"
                base_result["detail"] = f"Segment OK ({len(body)} bytes, {ct[:50]})"
            else:
                base_result["status"] = "manifest_only"
                base_result["detail"] = f"Segment bytes received but unusual content-type: {ct[:60]}"
            return base_result

    except httpx.TimeoutException:
        base_result["response_time_ms"] = int(VALIDATE_TIMEOUT * 1000)
        base_result["status"] = "timeout"
        base_result["detail"] = f"No response within {int(VALIDATE_TIMEOUT)}s"
        return base_result
    except httpx.ConnectError:
        base_result["response_time_ms"] = _ms(start)
        base_result["status"] = "offline"
        base_result["detail"] = "Connection error"
        return base_result
    except Exception as e:
        base_result["response_time_ms"] = _ms(start)
        base_result["status"] = "error"
        base_result["detail"] = str(e)[:200]
        return base_result


async def deep_validate_radio(url: str) -> dict[str, Any]:
    """Read first bytes of stream; verify audio-related content type when present."""
    start = time.monotonic()
    out: dict[str, Any] = {"status": "offline", "detail": "", "response_time_ms": 0}
    if not url or not url.strip():
        out["detail"] = "No URL"
        out["response_time_ms"] = _ms(start)
        return out

    try:
        async with _client() as client:
            async with client.stream("GET", url.strip(), headers=VALIDATE_HEADERS) as response:
                out["response_time_ms"] = _ms(start)
                if response.status_code in (403, 451):
                    body_peek = b""
                    try:
                        body_peek = await response.aread(512)
                    except Exception:
                        pass
                    if _geo_hint(response.status_code, body_peek.decode("utf-8", errors="ignore")):
                        out["status"] = "geo_blocked"
                        out["detail"] = f"HTTP {response.status_code} (likely geo/restriction)"
                        return out
                    out["status"] = "offline"
                    out["detail"] = f"HTTP {response.status_code}"
                    return out

                if response.status_code >= 400:
                    out["status"] = "offline"
                    out["detail"] = f"HTTP {response.status_code}"
                    return out

                ct = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
                read_total = 0
                buf = b""
                async for chunk in response.aiter_bytes():
                    buf += chunk
                    read_total += len(chunk)
                    if read_total >= 8192:
                        break

                out["response_time_ms"] = _ms(start)
                if read_total < 256:
                    out["status"] = "offline"
                    out["detail"] = "Insufficient stream data"
                    return out

                if ct.startswith("text/html"):
                    out["status"] = "offline"
                    out["detail"] = "HTML response (not audio stream)"
                    return out

                audio_like = (
                    any(ct.startswith(p) for p in AUDIO_CT_PREFIXES)
                    or ct in AUDIO_CT_EXACT
                    or "octet-stream" in ct
                    or ct == ""
                )
                if not audio_like:
                    out["status"] = "error"
                    out["detail"] = f"Unexpected content-type: {ct[:60]}"
                    return out

                out["status"] = "verified"
                out["detail"] = f"Stream OK ({read_total} bytes, {ct or 'unknown type'})"
                return out

    except httpx.TimeoutException:
        out["response_time_ms"] = int(VALIDATE_TIMEOUT * 1000)
        out["status"] = "timeout"
        out["detail"] = f"No response within {int(VALIDATE_TIMEOUT)}s"
        return out
    except httpx.ConnectError:
        out["response_time_ms"] = _ms(start)
        out["status"] = "offline"
        out["detail"] = "Connection error"
        return out
    except Exception as e:
        out["response_time_ms"] = _ms(start)
        out["status"] = "error"
        out["detail"] = str(e)[:200]
        return out


async def _channel_stream_url(session: AsyncSession, channel: Channel) -> str:
    if channel.stream_url and channel.stream_url.strip():
        return channel.stream_url.strip()
    row = (
        await session.execute(select(Stream.url).where(Stream.channel_id == channel.id).limit(1))
    ).first()
    return (row[0] or "").strip() if row else ""


async def _validate_and_update_channel(channel_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    async with async_session() as session:
        ch = (
            await session.execute(select(Channel).where(Channel.id == channel_id))
        ).scalar_one_or_none()
        if not ch:
            return {"skipped": True}

        url = await _channel_stream_url(session, ch)
        if not url:
            await session.execute(
                update(Channel)
                .where(Channel.id == channel_id)
                .values(
                    health_status="offline",
                    health_checked_at=now,
                    last_validated_at=now,
                )
            )
            await session.commit()
            return {"status": "offline", "channel_id": channel_id}

        if ".m3u8" in url:
            result = await deep_validate_hls(url)
        else:
            result = await probe_stream(url)

        await session.execute(
            update(Channel)
            .where(Channel.id == channel_id)
            .values(
                health_status=result["status"],
                health_checked_at=now,
                last_validated_at=now,
            )
        )
        await session.commit()
        return {"status": result["status"], "channel_id": channel_id}


async def _validate_and_update_radio(station_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    async with async_session() as session:
        st = (
            await session.execute(select(RadioStation).where(RadioStation.id == station_id))
        ).scalar_one_or_none()
        if not st:
            return {"skipped": True}

        url = (st.url_resolved or "").strip() or (st.url or "").strip()
        if not url:
            await session.execute(
                update(RadioStation)
                .where(RadioStation.id == station_id)
                .values(
                    health_status="offline",
                    health_checked_at=now,
                    last_check_ok=False,
                )
            )
            await session.commit()
            return {"status": "offline", "station_id": station_id}

        result = await deep_validate_radio(url)
        verified = result["status"] == "verified"

        await session.execute(
            update(RadioStation)
            .where(RadioStation.id == station_id)
            .values(
                health_status=result["status"],
                health_checked_at=now,
                last_check_ok=verified,
            )
        )
        await session.commit()
        return {"status": result["status"], "station_id": station_id}


async def validate_all_channels(
    db_session: AsyncSession,
    batch_size: int = 50,
    concurrency: int = 5,
) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc).isoformat()
    stats: dict[str, Any] = {
        "processed": 0,
        "batches": 0,
        "by_status": {},
    }
    sem = asyncio.Semaphore(concurrency)

    async def run_one(cid: str):
        async with sem:
            return await _validate_and_update_channel(cid)

    batch_idx = 0
    while True:
        q = (
            select(Channel.id)
            .where((Channel.health_checked_at < cutoff) | (Channel.health_checked_at == "") | (Channel.health_checked_at.is_(None)))
            .order_by(Channel.health_checked_at.asc().nullsfirst())
            .limit(batch_size)
        )
        rows = (await db_session.execute(q)).all()
        if not rows:
            break

        ids = [r[0] for r in rows]
        batch_idx += 1
        results = await asyncio.gather(*[run_one(i) for i in ids])

        for r in results:
            if r.get("skipped"):
                continue
            stats["processed"] += 1
            st = r.get("status", "unknown")
            stats["by_status"][st] = stats["by_status"].get(st, 0) + 1

        stats["batches"] = batch_idx
        logger.info(
            "Channel validation batch %d: size=%d cumulative_processed=%d",
            batch_idx,
            len(ids),
            stats["processed"],
        )

    return stats


async def validate_all_radio(
    db_session: AsyncSession,
    batch_size: int = 50,
    concurrency: int = 5,
) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc).isoformat()
    stats: dict[str, Any] = {
        "processed": 0,
        "batches": 0,
        "by_status": {},
    }
    sem = asyncio.Semaphore(concurrency)

    async def run_one(sid: str):
        async with sem:
            return await _validate_and_update_radio(sid)

    batch_idx = 0
    while True:
        q = (
            select(RadioStation.id)
            .where((RadioStation.health_checked_at < cutoff) | (RadioStation.health_checked_at == "") | (RadioStation.health_checked_at.is_(None)))
            .order_by(RadioStation.health_checked_at.asc().nullsfirst())
            .limit(batch_size)
        )
        rows = (await db_session.execute(q)).all()
        if not rows:
            break

        ids = [r[0] for r in rows]
        batch_idx += 1
        results = await asyncio.gather(*[run_one(i) for i in ids])

        for r in results:
            if r.get("skipped"):
                continue
            stats["processed"] += 1
            st = r.get("status", "unknown")
            stats["by_status"][st] = stats["by_status"].get(st, 0) + 1

        stats["batches"] = batch_idx
        logger.info(
            "Radio validation batch %d: size=%d cumulative_processed=%d",
            batch_idx,
            len(ids),
            stats["processed"],
        )

    return stats


_CHANNEL_VERIFIED = ("verified", "online")
_CHANNEL_OFFLINE = ("offline", "manifest_only", "timeout", "error", "geo_blocked")
_RADIO_VERIFIED = ("verified",)
_RADIO_OFFLINE = ("offline", "manifest_only", "timeout", "error", "geo_blocked")


async def get_validator_status(db_session: AsyncSession) -> dict[str, Any]:
    """Aggregate channel/radio validation counts and last check timestamps in two queries."""
    from sqlalchemy import text

    ch_row = (await db_session.execute(text("""
        SELECT
            count(*),
            count(*) FILTER (WHERE health_status IN ('verified','online')),
            count(*) FILTER (WHERE health_status IN ('offline','manifest_only','timeout','error','geo_blocked')),
            max(health_checked_at),
            max(last_validated_at)
        FROM channels
    """))).one()

    r_row = (await db_session.execute(text("""
        SELECT
            count(*),
            count(*) FILTER (WHERE health_status = 'verified'),
            count(*) FILTER (WHERE health_status IN ('offline','manifest_only','timeout','error','geo_blocked')),
            max(health_checked_at)
        FROM radio_stations
    """))).one()

    ch_total, ch_verified, ch_offline = ch_row[0], ch_row[1], ch_row[2]
    r_total, r_verified, r_offline = r_row[0], r_row[1], r_row[2]

    stamps = [s for s in (ch_row[3], ch_row[4], r_row[3]) if s]
    last_cycle_at = max(stamps) if stamps else ""

    return {
        "channels": {
            "total": int(ch_total),
            "verified": int(ch_verified),
            "offline": int(ch_offline),
            "unknown": max(0, int(ch_total) - int(ch_verified) - int(ch_offline)),
        },
        "radio": {
            "total": int(r_total),
            "verified": int(r_verified),
            "offline": int(r_offline),
            "unknown": max(0, int(r_total) - int(r_verified) - int(r_offline)),
        },
        "last_validation_cycle_at": last_cycle_at or "",
    }
