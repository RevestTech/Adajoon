from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import CategoryOut, CountryOut, StatsOut
from app.services.channel_service import (
    get_categories_with_counts, get_countries_with_counts, get_stats,
)

router = APIRouter(prefix="/api", tags=["metadata"])


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    rows = await get_categories_with_counts(db)
    return [CategoryOut(id=r.id, name=r.name, channel_count=r.channel_count) for r in rows]


@router.get("/countries", response_model=list[CountryOut])
async def list_countries(db: AsyncSession = Depends(get_db)):
    rows = await get_countries_with_counts(db)
    return [
        CountryOut(code=r.code, name=r.name, flag=r.flag, channel_count=r.channel_count)
        for r in rows
    ]


@router.get("/stats", response_model=StatsOut)
async def stats(db: AsyncSession = Depends(get_db)):
    return await get_stats(db)
