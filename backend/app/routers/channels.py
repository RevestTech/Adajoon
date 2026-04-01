import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    ChannelOut, ChannelSearchParams, PaginatedChannels, StreamOut
)
from app.services.channel_service import (
    search_channels, get_channel_by_id, get_channel_streams
)

router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.get("", response_model=PaginatedChannels)
async def list_channels(
    query: str | None = Query(None, description="Search term"),
    category: str | None = Query(None),
    country: str | None = Query(None),
    language: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(40, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    params = ChannelSearchParams(
        query=query, category=category, country=country,
        language=language, page=page, per_page=per_page,
    )
    channels, total = await search_channels(db, params)
    return PaginatedChannels(
        channels=[ChannelOut.model_validate(c) for c in channels],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=math.ceil(total / per_page) if total else 0,
    )


@router.get("/{channel_id}", response_model=ChannelOut)
async def get_channel(channel_id: str, db: AsyncSession = Depends(get_db)):
    channel = await get_channel_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return ChannelOut.model_validate(channel)


@router.get("/{channel_id}/streams", response_model=list[StreamOut])
async def get_streams(channel_id: str, db: AsyncSession = Depends(get_db)):
    streams = await get_channel_streams(db, channel_id)
    return [StreamOut.model_validate(s) for s in streams]
