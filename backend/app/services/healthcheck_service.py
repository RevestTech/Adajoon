import asyncio
import logging
import time
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Channel, Stream

logger = logging.getLogger(__name__)

PROBE_TIMEOUT = 10
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
}


async def probe_stream(url: str) -> dict:
    """Probe a stream URL and return status info."""
    start = time.monotonic()
    result = {"url": url, "status": "offline", "detail": "", "response_time_ms": 0}

    try:
        async with httpx.AsyncClient(
            timeout=PROBE_TIMEOUT,
            follow_redirects=True,
            headers=COMMON_HEADERS,
            verify=False,
        ) as client:
            if ".m3u8" in url:
                resp = await client.get(url)
                elapsed = int((time.monotonic() - start) * 1000)
                result["response_time_ms"] = elapsed

                if resp.status_code == 200:
                    body = resp.text[:2000]
                    if "#EXTM3U" in body or "#EXTINF" in body or "#EXT-X" in body:
                        result["status"] = "online"
                        result["detail"] = "HLS manifest valid"
                    else:
                        result["status"] = "error"
                        result["detail"] = "Response is not a valid HLS manifest"
                else:
                    result["status"] = "offline"
                    result["detail"] = f"HTTP {resp.status_code}"
            else:
                resp = await client.head(url)
                elapsed = int((time.monotonic() - start) * 1000)
                result["response_time_ms"] = elapsed

                if resp.status_code < 400:
                    result["status"] = "online"
                    content_type = resp.headers.get("content-type", "")
                    result["detail"] = f"HTTP {resp.status_code}, {content_type[:60]}"
                elif resp.status_code == 405:
                    resp = await client.get(url, headers={"Range": "bytes=0-1024"})
                    elapsed = int((time.monotonic() - start) * 1000)
                    result["response_time_ms"] = elapsed
                    if resp.status_code < 400:
                        result["status"] = "online"
                        result["detail"] = f"HTTP {resp.status_code} (GET fallback)"
                    else:
                        result["status"] = "offline"
                        result["detail"] = f"HTTP {resp.status_code}"
                else:
                    result["status"] = "offline"
                    result["detail"] = f"HTTP {resp.status_code}"

    except httpx.TimeoutException:
        result["response_time_ms"] = PROBE_TIMEOUT * 1000
        result["status"] = "timeout"
        result["detail"] = f"No response within {PROBE_TIMEOUT}s"
    except httpx.ConnectError:
        result["response_time_ms"] = int((time.monotonic() - start) * 1000)
        result["status"] = "offline"
        result["detail"] = "Connection refused"
    except Exception as e:
        result["response_time_ms"] = int((time.monotonic() - start) * 1000)
        result["status"] = "error"
        result["detail"] = str(e)[:200]

    return result


async def check_channel(db: AsyncSession, channel_id: str) -> dict:
    """Check health of a specific channel's stream."""
    ch = (await db.execute(select(Channel).where(Channel.id == channel_id))).scalar_one_or_none()
    if not ch:
        return {"error": "Channel not found"}

    url = ch.stream_url
    if not url:
        streams = (await db.execute(
            select(Stream).where(Stream.channel_id == channel_id).limit(1)
        )).scalar_one_or_none()
        if streams:
            url = streams.url

    if not url:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            update(Channel)
            .where(Channel.id == channel_id)
            .values(health_status="offline", health_checked_at=now)
        )
        await db.commit()
        return {
            "channel_id": channel_id,
            "stream_url": "",
            "status": "offline",
            "response_time_ms": 0,
            "detail": "No stream URL available",
            "checked_at": now,
        }

    result = await probe_stream(url)
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        update(Channel)
        .where(Channel.id == channel_id)
        .values(health_status=result["status"], health_checked_at=now)
    )
    await db.commit()

    return {
        "channel_id": channel_id,
        "stream_url": url,
        "status": result["status"],
        "response_time_ms": result["response_time_ms"],
        "detail": result["detail"],
        "checked_at": now,
    }


async def check_channels_batch(db: AsyncSession, channel_ids: list[str], concurrency: int = 10) -> list[dict]:
    """Check health of multiple channels concurrently with isolated sessions."""
    from app.database import async_session

    semaphore = asyncio.Semaphore(concurrency)

    async def limited_check(cid):
        async with semaphore:
            async with async_session() as session:
                return await check_channel(session, cid)

    tasks = [limited_check(cid) for cid in channel_ids]
    return await asyncio.gather(*tasks)
