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


async def _read_capped(response: httpx.Response, cap: int) -> bytes:
    """Read at most `cap` bytes from a streamed response, then stop.

    A stream source that ignores HEAD/Range semantics and keeps pushing an
    unbounded live feed must never be allowed to fill up process memory -
    this was traced to the validator worker's intermittent crash-restarts
    (httpx's non-streaming get()/head() fully buffer whatever body a server
    sends, regardless of the request method or headers)."""
    chunks = []
    total = 0
    async for chunk in response.aiter_bytes():
        remaining = cap - total
        if remaining <= 0:
            break
        if len(chunk) > remaining:
            chunk = chunk[:remaining]
        chunks.append(chunk)
        total += len(chunk)
        if total >= cap:
            break
    return b"".join(chunks)


async def probe_stream(url: str) -> dict:
    """Probe a stream URL and return status info."""
    try:
        return await asyncio.wait_for(_probe_stream_inner(url), timeout=PROBE_TIMEOUT)
    except (TimeoutError, asyncio.TimeoutError):
        return {
            "url": url,
            "status": "timeout",
            "detail": f"No response within {PROBE_TIMEOUT}s",
            "response_time_ms": PROBE_TIMEOUT * 1000,
        }


async def _probe_stream_inner(url: str) -> dict:
    """The actual probe.

    Two independent bounds are both needed here, for two different failure
    modes seen in production:

    - A live stream whose server ignores Range/HEAD and just trickles bytes
      forever bounds neither request count nor total size - httpx's own
      `timeout` only bounds the gap between reads, not the overall call, so
      it never fires on its own. The outer wait_for in probe_stream() is
      what bounds wall-clock time for this case.
    - A server that ignores HEAD/Range and instead sends its full (or
      unbounded live) body fast, well within that same timeout window,
      doesn't trip the wait_for at all - but client.get()/head() buffer
      whatever a server sends in full before returning, so a handful of
      these running concurrently was enough to crash the validator worker.
      Every read below goes through client.stream() (closed before the
      body is drained) and _read_capped, so no call here can ever buffer
      more than a couple KB regardless of how much a server actually sends.
    """
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
                async with client.stream("GET", url) as resp:
                    result["response_time_ms"] = int((time.monotonic() - start) * 1000)
                    status_code = resp.status_code
                    body = await _read_capped(resp, 2000) if status_code == 200 else b""

                if status_code == 200:
                    text = body[:2000].decode("utf-8", errors="ignore")
                    if "#EXTM3U" in text or "#EXTINF" in text or "#EXT-X" in text:
                        result["status"] = "online"
                        result["detail"] = "HLS manifest valid"
                    else:
                        result["status"] = "error"
                        result["detail"] = "Response is not a valid HLS manifest"
                else:
                    result["status"] = "offline"
                    result["detail"] = f"HTTP {status_code}"
            else:
                async with client.stream("HEAD", url) as resp:
                    result["response_time_ms"] = int((time.monotonic() - start) * 1000)
                    status_code = resp.status_code
                    content_type = resp.headers.get("content-type", "")

                if status_code < 400:
                    result["status"] = "online"
                    result["detail"] = f"HTTP {status_code}, {content_type[:60]}"
                elif status_code == 405:
                    async with client.stream(
                        "GET", url, headers={"Range": "bytes=0-1024"}
                    ) as resp2:
                        result["response_time_ms"] = int(
                            (time.monotonic() - start) * 1000
                        )
                        status_code2 = resp2.status_code
                        await _read_capped(resp2, 1025)
                    if status_code2 < 400:
                        result["status"] = "online"
                        result["detail"] = f"HTTP {status_code2} (GET fallback)"
                    else:
                        result["status"] = "offline"
                        result["detail"] = f"HTTP {status_code2}"
                else:
                    result["status"] = "offline"
                    result["detail"] = f"HTTP {status_code}"

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
    ch = (
        await db.execute(select(Channel).where(Channel.id == channel_id))
    ).scalar_one_or_none()
    if not ch:
        return {"error": "Channel not found"}

    url = ch.stream_url
    if not url:
        streams = (
            await db.execute(
                select(Stream).where(Stream.channel_id == channel_id).limit(1)
            )
        ).scalar_one_or_none()
        if streams:
            url = streams.url

    if not url:
        now = datetime.now(timezone.utc)
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
            "checked_at": now.isoformat(),
        }

    result = await probe_stream(url)
    now = datetime.now(timezone.utc)

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
        "checked_at": now.isoformat(),
    }


async def check_channels_batch(
    db: AsyncSession, channel_ids: list[str], concurrency: int = 10
) -> list[dict]:
    """Check health of multiple channels concurrently with isolated sessions."""
    from app.database import async_session

    semaphore = asyncio.Semaphore(concurrency)

    async def limited_check(cid):
        async with semaphore:
            async with async_session() as session:
                return await check_channel(session, cid)

    tasks = [limited_check(cid) for cid in channel_ids]
    return await asyncio.gather(*tasks)
