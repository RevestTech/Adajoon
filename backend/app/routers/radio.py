import logging
import math

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    RadioStationOut, RadioSearchParams, PaginatedRadio,
    RadioTagOut, RadioCountryOut,
)
from app.services.radio_service import (
    search_radio, get_radio_tags, get_radio_countries,
)
from app.redis_client import cache_get, cache_set

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/radio", tags=["radio"])

CACHE_TTL = 300  # 5 minutes
TAGS_CACHE_TTL = 3600  # 1 hour for expensive tags query


@router.get("/stations", response_model=PaginatedRadio)
async def list_radio_stations(
    query: str | None = Query(None, description="Search term"),
    tag: str | None = Query(None),
    country: str | None = Query(None),
    language: str | None = Query(None),
    working_only: bool = Query(False),
    status: str | None = Query(None, description="Filter by health status: verified, live, or hide_offline"),
    page: int = Query(1, ge=1),
    per_page: int = Query(40, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    params = RadioSearchParams(
        query=query, tag=tag, country=country,
        language=language, working_only=working_only,
        status=status, page=page, per_page=per_page,
    )
    stations, total = await search_radio(db, params)
    return PaginatedRadio(
        stations=[RadioStationOut.model_validate(s) for s in stations],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=math.ceil(total / per_page) if total else 0,
    )


STATIC_TAGS = [
    {"name": "music", "station_count": 5000},
    {"name": "pop", "station_count": 3500},
    {"name": "news", "station_count": 2800},
    {"name": "rock", "station_count": 2500},
    {"name": "talk", "station_count": 2200},
    {"name": "jazz", "station_count": 1800},
    {"name": "classical", "station_count": 1500},
    {"name": "electronic", "station_count": 1400},
    {"name": "dance", "station_count": 1300},
    {"name": "country", "station_count": 1200},
    {"name": "hip hop", "station_count": 1100},
    {"name": "sports", "station_count": 1000},
    {"name": "oldies", "station_count": 950},
    {"name": "80s", "station_count": 900},
    {"name": "90s", "station_count": 850},
    {"name": "christian", "station_count": 800},
    {"name": "alternative", "station_count": 750},
    {"name": "latin", "station_count": 700},
    {"name": "blues", "station_count": 650},
    {"name": "variety", "station_count": 600},
]

@router.get("/tags")
async def list_radio_tags():
    """
    Get popular radio tags/genres.
    Returns a static curated list for performance.
    """
    return STATIC_TAGS


@router.get("/countries", response_model=list[RadioCountryOut])
async def list_radio_countries(db: AsyncSession = Depends(get_db)):
    try:
        cached = await cache_get("radio_countries")
        if cached is not None:
            return cached
        rows = await get_radio_countries(db)
        data = [
            RadioCountryOut(country=r.country, country_code=r.country_code, station_count=r.station_count)
            for r in rows
        ]
        # Convert Pydantic models to dicts for caching
        await cache_set("radio_countries", [d.model_dump() for d in data], CACHE_TTL)
        return data
    except Exception as e:
        logger.error(f"Error in list_radio_countries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch radio countries: {str(e)}")
