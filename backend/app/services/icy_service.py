"""ICY (Shoutcast/Icecast) in-band metadata - the "now playing" track title
embedded directly in a radio stream's audio bytes, not available via any REST
API. Fetching it means briefly acting as a streaming audio client: request
the stream with Icy-MetaData: 1, skip icy-metaint bytes of audio, read one
metadata block, then close - never keep the connection open.
"""

import asyncio
import logging
import re

import httpx

logger = logging.getLogger(__name__)

ICY_TIMEOUT = 4.0
# Sanity cap on icy-metaint so a malformed/hostile response can't make us
# buffer an unbounded amount of "audio" before giving up.
ICY_MAX_METAINT = 1_000_000

_STREAM_TITLE_RE = re.compile(rb"StreamTitle='([^']*)'")


class _ByteReader:
    """Buffers an httpx streaming response's arbitrarily-sized chunks so
    callers can read an exact byte count - icy-metaint framing doesn't align
    to HTTP chunk boundaries."""

    def __init__(self, aiter):
        self._aiter = aiter
        self._buf = b""

    async def read(self, n: int) -> bytes:
        while len(self._buf) < n:
            try:
                chunk = await self._aiter.__anext__()
            except StopAsyncIteration:
                break
            self._buf += chunk
        result, self._buf = self._buf[:n], self._buf[n:]
        return result


async def fetch_icy_title(stream_url: str) -> str | None:
    """Current StreamTitle from a station's stream, or None if it doesn't
    support ICY metadata (the common case - many Shoutcast/Icecast servers
    don't enable it) or couldn't be reached in time."""
    if not stream_url:
        return None
    try:
        async with httpx.AsyncClient(
            timeout=ICY_TIMEOUT, follow_redirects=True
        ) as client:
            async with client.stream(
                "GET",
                stream_url,
                headers={"Icy-MetaData": "1", "User-Agent": "Adajoon/1.0"},
            ) as response:
                if response.status_code >= 400:
                    return None
                metaint = response.headers.get("icy-metaint")
                if not metaint or not metaint.isdigit():
                    return None
                metaint = int(metaint)
                if metaint <= 0 or metaint > ICY_MAX_METAINT:
                    return None

                reader = _ByteReader(response.aiter_bytes())
                await reader.read(metaint)
                length_byte = await reader.read(1)
                if not length_byte:
                    return None
                meta_len = length_byte[0] * 16
                if meta_len == 0:
                    return None
                meta = await reader.read(meta_len)
                match = _STREAM_TITLE_RE.search(meta)
                if not match:
                    return None
                title = match.group(1).decode("utf-8", errors="replace").strip()
                return title or None
    except (httpx.HTTPError, asyncio.TimeoutError, OSError) as e:
        logger.debug("ICY fetch failed for %s: %s", stream_url, e)
        return None
