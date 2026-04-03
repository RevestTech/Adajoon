"""Watch history endpoints."""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import get_db
from app.models import User, WatchHistory
from app.routers.auth import get_current_user
from app.csrf import verify_csrf_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/history", tags=["history"])


class WatchHistoryItem(BaseModel):
    item_type: str = Field(..., pattern="^(tv|radio)$")
    item_id: str
    item_name: str
    item_logo: Optional[str] = ""
    duration_seconds: int = 0


class WatchHistoryResponse(BaseModel):
    id: int
    item_type: str
    item_id: str
    item_name: str
    item_logo: str
    watched_at: datetime
    duration_seconds: int


@router.post("/record")
async def record_watch_history(
    item: WatchHistoryItem,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Record or update a watch history entry."""
    try:
        # Upsert: if same user + item exists in last 1 hour, update it; otherwise insert
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        stmt = pg_insert(WatchHistory).values(
            user_id=user.id,
            item_type=item.item_type,
            item_id=item.item_id,
            item_name=item.item_name,
            item_logo=item.item_logo or "",
            watched_at=datetime.now(timezone.utc),
            duration_seconds=item.duration_seconds,
        )
        
        # Update if recent duplicate exists
        stmt = stmt.on_conflict_do_update(
            constraint="ix_watch_history_user_item_recent",
            set_={
                "watched_at": datetime.now(timezone.utc),
                "duration_seconds": stmt.excluded.duration_seconds,
                "item_name": stmt.excluded.item_name,
                "item_logo": stmt.excluded.item_logo,
            },
        )
        
        await db.execute(stmt)
        await db.commit()
        
        return {"status": "recorded"}
    except Exception as e:
        logger.error(f"Failed to record watch history: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record watch history"
        )


@router.get("/", response_model=list[WatchHistoryResponse])
async def get_watch_history(
    item_type: Optional[str] = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get watch history for the current user."""
    query = select(WatchHistory).where(WatchHistory.user_id == user.id)
    
    if item_type and item_type in ("tv", "radio"):
        query = query.where(WatchHistory.item_type == item_type)
    
    query = query.order_by(desc(WatchHistory.watched_at)).limit(min(limit, 200))
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return [
        WatchHistoryResponse(
            id=item.id,
            item_type=item.item_type,
            item_id=item.item_id,
            item_name=item.item_name,
            item_logo=item.item_logo,
            watched_at=item.watched_at,
            duration_seconds=item.duration_seconds,
        )
        for item in items
    ]


@router.delete("/")
async def clear_watch_history(
    item_type: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Clear watch history for the current user."""
    try:
        query = delete(WatchHistory).where(WatchHistory.user_id == user.id)
        
        if item_type and item_type in ("tv", "radio"):
            query = query.where(WatchHistory.item_type == item_type)
        
        result = await db.execute(query)
        await db.commit()
        
        return {"status": "cleared", "deleted_count": result.rowcount}
    except Exception as e:
        logger.error(f"Failed to clear watch history: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear watch history"
        )


@router.delete("/{history_id}")
async def delete_watch_history_item(
    history_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Delete a specific watch history item."""
    result = await db.execute(
        delete(WatchHistory)
        .where(WatchHistory.id == history_id)
        .where(WatchHistory.user_id == user.id)
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History item not found"
        )
    
    await db.commit()
    return {"status": "deleted"}
