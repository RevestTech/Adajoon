"""EPG (Electronic Program Guide) API endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.epg_service import get_channel_epg, get_now_next, search_on_now

router = APIRouter(prefix="/api/epg", tags=["epg"])


@router.get("/now")
async def epg_now(
    channel_id: str | None = Query(None),
    q: str | None = Query(None, max_length=200),
    category: str | None = Query(None, max_length=100),
    limit: int = Query(40, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Current (+ next) for one channel, or programmes airing now matching q/category."""
    if channel_id:
        return await get_now_next(db, channel_id)
    if not q and not category:
        raise HTTPException(
            status_code=400,
            detail="Provide channel_id, or q/category for on-now search",
        )
    items = await search_on_now(db, q=q, category=category, limit=limit)
    return {"items": items, "total": len(items)}


@router.get("/channels/{channel_id}")
async def channel_epg_schedule(
    channel_id: str,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    programmes = await get_channel_epg(db, channel_id, start=start, end=end)
    return {"channel_id": channel_id, "programmes": programmes}
