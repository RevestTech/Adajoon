import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import CategoryOut, CountryOut, StatsOut
from app.services.channel_service import (
    get_categories_with_counts, get_countries_with_counts, get_stats,
)
from app.redis_client import cache_get, cache_set

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["metadata"])

CACHE_TTL = 300  # 5 minutes


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    try:
        logger.info("Categories endpoint called")
        cached = await cache_get("categories")
        if cached is not None:
            logger.info("Returning cached categories")
            return cached
        logger.info("Fetching categories from database")
        rows = await get_categories_with_counts(db)
        logger.info(f"Got {len(rows)} categories from database")
        data = [
            CategoryOut(
                id=r.id,
                name=r.name,
                channel_count=int(r.channel_count or 0),
                live_count=int(r.live_count or 0),
                verified_count=int(r.verified_count or 0),
            )
            for r in rows
        ]
        await cache_set("categories", [d.model_dump() for d in data], CACHE_TTL)
        logger.info("Categories cached and returning")
        return data
    except Exception as e:
        logger.error(f"Error in list_categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")


@router.get("/countries", response_model=list[CountryOut])
async def list_countries(db: AsyncSession = Depends(get_db)):
    cached = await cache_get("countries")
    if cached is not None:
        return cached
    rows = await get_countries_with_counts(db)
    data = [
        CountryOut(
            code=r.code,
            name=r.name,
            flag=r.flag or "",
            channel_count=int(r.channel_count or 0),
            live_count=int(r.live_count or 0),
            verified_count=int(r.verified_count or 0),
        )
        for r in rows
    ]
    await cache_set("countries", [d.model_dump() for d in data], CACHE_TTL)
    return data


@router.get("/stats", response_model=StatsOut)
async def stats(db: AsyncSession = Depends(get_db)):
    cached = await cache_get("stats")
    if cached is not None:
        return cached
    data = await get_stats(db)
    await cache_set("stats", data, CACHE_TTL)
    return data
