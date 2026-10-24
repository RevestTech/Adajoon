"""EPG schedule and now/next endpoints."""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    EpgNowBatchResponse,
    EpgNowResponse,
    EpgOnNowItem,
    EpgOnNowResponse,
    EpgProgrammeOut,
    EpgScheduleBatchResponse,
    EpgScheduleResponse,
)
from app.services.epg_service import (
    get_channel_schedule,
    get_now_batch,
    get_now_next,
    get_schedule_batch,
    resolve_schedule_window,
    search_on_now,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/epg", tags=["epg"])
channels_epg_router = APIRouter(prefix="/api/channels", tags=["epg"])


def _programme_out(row) -> EpgProgrammeOut:
    return EpgProgrammeOut.model_validate(row)


@channels_epg_router.get("/{channel_id}/epg", response_model=EpgScheduleResponse)
async def channel_epg_schedule(
    channel_id: str,
    from_: datetime | None = Query(
        None, alias="from", description="Window start (ISO)"
    ),
    to: datetime | None = Query(None, description="Window end (ISO)"),
    db: AsyncSession = Depends(get_db),
) -> EpgScheduleResponse:
    """Schedule window for a channel (default: now → +24h)."""
    try:
        window_from, window_to = resolve_schedule_window(from_, to)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    rows = await get_channel_schedule(db, channel_id, window_from, window_to)
    return EpgScheduleResponse(
        channel_id=channel_id,
        from_at=window_from,
        to_at=window_to,
        programmes=[_programme_out(r) for r in rows],
    )


@router.get("/now-batch", response_model=EpgNowBatchResponse)
async def epg_now_batch(
    channel_ids: str = Query(..., description="Comma-separated channel ids"),
    db: AsyncSession = Depends(get_db),
) -> EpgNowBatchResponse:
    """Current programme for each of a page of channel tiles, in one query."""
    ids = [c.strip() for c in channel_ids.split(",") if c.strip()]
    if not ids:
        return EpgNowBatchResponse(items={})
    by_channel = await get_now_batch(db, ids)
    return EpgNowBatchResponse(
        items={cid: _programme_out(p) for cid, p in by_channel.items()}
    )


@router.get("/schedule-batch", response_model=EpgScheduleBatchResponse)
async def epg_schedule_batch(
    channel_ids: str = Query(..., description="Comma-separated channel ids"),
    from_: datetime | None = Query(
        None, alias="from", description="Window start (ISO)"
    ),
    to: datetime | None = Query(None, description="Window end (ISO)"),
    db: AsyncSession = Depends(get_db),
) -> EpgScheduleBatchResponse:
    """Channel x time schedule for a page of channels, for the EPG grid view."""
    ids = [c.strip() for c in channel_ids.split(",") if c.strip()]
    if not ids:
        return EpgScheduleBatchResponse(
            from_at=datetime.now(), to_at=datetime.now(), items={}
        )

    try:
        window_from, window_to = resolve_schedule_window(from_, to)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    by_channel = await get_schedule_batch(db, ids, window_from, window_to)
    return EpgScheduleBatchResponse(
        from_at=window_from,
        to_at=window_to,
        items={
            cid: [_programme_out(p) for p in programmes]
            for cid, programmes in by_channel.items()
        },
    )


@router.get("/now")
async def epg_now(
    channel_id: str | None = Query(None, description="Channel id for now/next"),
    q: str | None = Query(None, description="Title/category substring for on-now"),
    category: str | None = Query(None, description="Category substring for on-now"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> EpgNowResponse | EpgOnNowResponse:
    """Current+next for one channel, or channels with matching programme airing now."""
    if channel_id:
        current, nxt = await get_now_next(db, channel_id)
        return EpgNowResponse(
            channel_id=channel_id,
            now=_programme_out(current) if current else None,
            next=_programme_out(nxt) if nxt else None,
        )

    if not q and not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide channel_id, q, or category",
        )

    try:
        rows = await search_on_now(db, q=q, category=category, limit=limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    return EpgOnNowResponse(
        items=[
            EpgOnNowItem(channel_id=r.channel_id, programme=_programme_out(r))
            for r in rows
        ],
        q=q,
        category=category,
    )
