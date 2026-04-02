import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import CategoryOut, CountryOut, StatsOut
from app.services.channel_service import (
    get_categories_with_counts, get_countries_with_counts, get_stats,
)

router = APIRouter(prefix="/api", tags=["metadata"])

_cache: dict[str, tuple[float, object]] = {}
CACHE_TTL = 300  # 5 minutes


def _get_cached(key: str):
    entry = _cache.get(key)
    if entry and (time.monotonic() - entry[0]) < CACHE_TTL:
        return entry[1]
    return None


def _set_cached(key: str, value):
    _cache[key] = (time.monotonic(), value)


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    cached = _get_cached("categories")
    if cached is not None:
        return cached
    rows = await get_categories_with_counts(db)
    data = [CategoryOut(id=r.id, name=r.name, channel_count=r.channel_count) for r in rows]
    _set_cached("categories", data)
    return data


@router.get("/countries", response_model=list[CountryOut])
async def list_countries(db: AsyncSession = Depends(get_db)):
    cached = _get_cached("countries")
    if cached is not None:
        return cached
    rows = await get_countries_with_counts(db)
    data = [
        CountryOut(code=r.code, name=r.name, flag=r.flag, channel_count=r.channel_count)
        for r in rows
    ]
    _set_cached("countries", data)
    return data


@router.get("/stats", response_model=StatsOut)
async def stats(db: AsyncSession = Depends(get_db)):
    cached = _get_cached("stats")
    if cached is not None:
        return cached
    data = await get_stats(db)
    _set_cached("stats", data)
    return data
