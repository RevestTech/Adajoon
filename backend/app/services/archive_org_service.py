"""Internet Archive (archive.org) lookup for admin-side movie import.

Unlike TMDb (metadata/posters only) or YouTube (admin pastes the URL by
hand), this returns a real, directly playable stream_url: archive.org's
public-domain "feature_films"-style items serve plain MP4 files over
HTTP with CORS enabled and range-request support - no API key, no auth,
legally in the clear since everything indexed here is public domain or
otherwise freely redistributable (that's the point of the collection).

No key required - archive.org's search and metadata endpoints are open.
"""

import asyncio
import logging
import urllib.parse

import httpx

logger = logging.getLogger(__name__)

SEARCH_URL = "https://archive.org/advancedsearch.php"
METADATA_URL = "https://archive.org/metadata"
THUMB_URL = "https://archive.org/services/img"

# archive.org's advancedsearch.php is occasionally slow (observed 10-15s on
# a cold query) - generous but bounded timeouts rather than a tight one that
# makes a legitimately slow-but-successful search look like a failure.
SEARCH_TIMEOUT = 20.0
METADATA_TIMEOUT = 10.0
# Bounds how many /metadata lookups run at once - fetched one-at-a-time
# would make this endpoint take limit*METADATA_TIMEOUT in the worst case.
METADATA_CONCURRENCY = 5

# Preferred video formats, in order - "...ia.mp4" derivatives tend to be a
# lower-bitrate re-encode of the same source, so a plain MPEG4/h.264 file
# of the same or larger size is preferred when both exist.
_VIDEO_FORMATS = ("MPEG4", "h.264", "512Kb MPEG4")
_SKIP_NAME_HINTS = ("thumbs", "sample", ".gif", ".srt", ".vtt")


def _pick_stream_file(files: list[dict]) -> dict | None:
    candidates = [
        f
        for f in files
        if f.get("format") in _VIDEO_FORMATS
        and not any(hint in f.get("name", "").lower() for hint in _SKIP_NAME_HINTS)
    ]
    if not candidates:
        return None
    # Largest file is the best-quality source among the preferred formats.
    return max(candidates, key=lambda f: int(f.get("size") or 0))


async def _fetch_candidate(
    client: httpx.AsyncClient, doc: dict, semaphore: asyncio.Semaphore
) -> dict | None:
    identifier = doc.get("identifier")
    if not identifier:
        return None

    try:
        async with semaphore:
            resp = await client.get(
                f"{METADATA_URL}/{identifier}", timeout=METADATA_TIMEOUT
            )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("archive.org metadata fetch failed for %s: %s", identifier, e)
        return None

    data = resp.json()
    stream_file = _pick_stream_file(data.get("files", []))
    if not stream_file:
        return None

    meta = data.get("metadata", {})
    year_raw = str(meta.get("year") or doc.get("year") or "")
    year = int(year_raw[:4]) if year_raw[:4].isdigit() else None

    encoded_name = urllib.parse.quote(stream_file["name"])
    return {
        "archive_id": identifier,
        "title": meta.get("title") or doc.get("title") or identifier,
        "year": year,
        "poster_url": f"{THUMB_URL}/{identifier}",
        "synopsis": (meta.get("description") or doc.get("description") or "")[:1000],
        "source": "archive.org",
        "stream_url": f"https://archive.org/download/{identifier}/{encoded_name}",
    }


async def search_movies(query: str, limit: int = 6) -> list[dict]:
    """Search archive.org's public-domain film collection by title.
    Over-fetches search results since not every indexed item has an
    actual playable video file, then filters down to ones that do -
    metadata lookups run concurrently (bounded) rather than one at a time,
    since archive.org itself can already be slow on the initial search."""
    params = {
        "q": f"title:({query}) AND mediatype:(movies)",
        "fl[]": ["identifier", "title", "year", "description"],
        "rows": str(limit * 2),
        "sort[]": "downloads desc",
        "output": "json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(SEARCH_URL, params=params, timeout=SEARCH_TIMEOUT)
        resp.raise_for_status()
        docs = resp.json().get("response", {}).get("docs", [])

        semaphore = asyncio.Semaphore(METADATA_CONCURRENCY)
        candidates = await asyncio.gather(
            *(_fetch_candidate(client, doc, semaphore) for doc in docs)
        )

    return [c for c in candidates if c][:limit]
