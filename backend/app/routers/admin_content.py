"""Admin-only content moderation endpoints for channels and radio stations.

The IPTV/radio sync jobs overwrite is_active/last_check_ok every run, so
that can't be used as a manual override; admin_hidden is separate and
sticky.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.csrf import verify_csrf_token
from app.database import get_db
from app.middleware.admin_required import require_admin
from app.models import Channel, RadioStation, User
from app.redis_client import cache_delete

router = APIRouter(prefix="/api/admin", tags=["admin", "content"])
logger = logging.getLogger(__name__)


def _ilike_pattern(raw: str) -> str:
    """Escape ILIKE wildcard/escape characters in user input so a search for
    literal `%`, `_`, or `\\` doesn't act as a wildcard."""
    escaped = raw.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@router.get("/channels/search")
async def admin_search_channels(
    q: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    pattern = _ilike_pattern(q)
    cond = Channel.name.ilike(pattern, escape="\\")
    total = (await db.execute(select(func.count(Channel.id)).where(cond))).scalar() or 0
    result = await db.execute(
        select(Channel)
        .where(cond)
        .order_by(Channel.name, Channel.id)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    channels = result.scalars().all()
    return {
        "channels": [
            {
                "id": c.id,
                "name": c.name,
                "country_code": c.country_code,
                "health_status": c.health_status,
                "admin_hidden": c.admin_hidden,
            }
            for c in channels
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.patch("/channels/{channel_id}/hidden")
async def admin_set_channel_hidden(
    channel_id: str,
    hidden: bool,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    channel.admin_hidden = hidden
    await db.commit()
    # Categories/countries/stats are cached (see routers/categories.py) and
    # their counts depend on admin_hidden - force a re-fetch on next read
    # instead of waiting out the TTL.
    for key in ("categories", "countries", "stats"):
        await cache_delete(key)
    logger.info(
        "Admin %s set channel %s admin_hidden=%s", admin_user.email, channel_id, hidden
    )
    return {"success": True, "admin_hidden": hidden}


@router.get("/radio/search")
async def admin_search_radio(
    q: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    pattern = _ilike_pattern(q)
    cond = RadioStation.name.ilike(pattern, escape="\\")
    total = (
        await db.execute(select(func.count(RadioStation.id)).where(cond))
    ).scalar() or 0
    result = await db.execute(
        select(RadioStation)
        .where(cond)
        .order_by(RadioStation.name, RadioStation.id)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    stations = result.scalars().all()
    return {
        "stations": [
            {
                "id": s.id,
                "name": s.name,
                "country_code": s.country_code,
                "health_status": s.health_status,
                "admin_hidden": s.admin_hidden,
            }
            for s in stations
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.patch("/radio/{station_id}/hidden")
async def admin_set_radio_hidden(
    station_id: str,
    hidden: bool,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    result = await db.execute(select(RadioStation).where(RadioStation.id == station_id))
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    station.admin_hidden = hidden
    await db.commit()
    for key in ("radio_countries", "stats"):
        await cache_delete(key)
    logger.info(
        "Admin %s set station %s admin_hidden=%s", admin_user.email, station_id, hidden
    )
    return {"success": True, "admin_hidden": hidden}
