"""TMDb (The Movie Database) lookup for admin-side poster art and metadata.

Free API - https://www.themoviedb.org/settings/api. Used only to help an
admin fill in a syndicated movie's poster_url/year/synopsis/genres when
adding it; Adajoon stores the result as plain fields on Movie, it doesn't
proxy TMDb at playback time.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TMDB_API_BASE = "https://api.themoviedb.org/3"
TMDB_POSTER_BASE = "https://image.tmdb.org/t/p/w500"

# Genre id -> name, fetched once and reused for the process lifetime (TMDb's
# genre list changes essentially never).
_genre_cache: dict[int, str] | None = None


class TmdbNotConfigured(Exception):
    """Raised when no TMDB_API_KEY is set."""


async def _get_genre_map(client: httpx.AsyncClient) -> dict[int, str]:
    global _genre_cache
    if _genre_cache is not None:
        return _genre_cache

    resp = await client.get(
        f"{TMDB_API_BASE}/genre/movie/list",
        params={"api_key": settings.tmdb_api_key},
    )
    resp.raise_for_status()
    data = resp.json()
    _genre_cache = {g["id"]: g["name"] for g in data.get("genres", [])}
    return _genre_cache


async def search_movies(query: str, limit: int = 8) -> list[dict]:
    """Search TMDb by title. Returns a list of candidate dicts shaped to
    drop straight into the admin MovieCreate form (title/year/poster_url/
    synopsis/genres)."""
    if not settings.tmdb_api_key:
        raise TmdbNotConfigured()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{TMDB_API_BASE}/search/movie",
            params={
                "api_key": settings.tmdb_api_key,
                "query": query,
                "include_adult": "false",
            },
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])[:limit]

        genre_map = await _get_genre_map(client)

    candidates = []
    for r in results:
        release_date = r.get("release_date") or ""
        year = int(release_date[:4]) if release_date[:4].isdigit() else None
        poster_path = r.get("poster_path") or ""
        genres = [genre_map[gid] for gid in r.get("genre_ids", []) if gid in genre_map]
        candidates.append(
            {
                "tmdb_id": r.get("id"),
                "title": r.get("title") or "",
                "year": year,
                "poster_url": f"{TMDB_POSTER_BASE}{poster_path}" if poster_path else "",
                "synopsis": r.get("overview") or "",
                "genres": ", ".join(genres),
            }
        )
    return candidates
