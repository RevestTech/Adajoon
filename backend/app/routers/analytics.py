"""
Analytics tracking endpoints for custom self-hosted analytics.
Receives events from frontend and stores in PostgreSQL.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AnalyticsEvent, User
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class AnalyticsEventPayload(BaseModel):
    event_name: str = Field(..., max_length=100)
    session_id: str = Field(..., max_length=255)
    properties: dict = Field(default_factory=dict)


@router.post("/track", status_code=status.HTTP_201_CREATED)
async def track_event(
    payload: AnalyticsEventPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    Track an analytics event.
    
    Events are stored in PostgreSQL with user_id (if authenticated),
    session_id, event_name, properties (JSONB), and timestamp.
    """
    try:
        # Add metadata to properties
        enriched_properties = {
            **payload.properties,
            "user_agent": request.headers.get("user-agent", ""),
            "ip_address": request.client.host if request.client else None,
        }
        
        event = AnalyticsEvent(
            user_id=current_user.id if current_user else None,
            session_id=payload.session_id,
            event_name=payload.event_name,
            properties=enriched_properties,
            created_at=datetime.now(timezone.utc),
        )
        
        db.add(event)
        await db.commit()
        
        return {"status": "ok", "event_id": event.id}
        
    except Exception as e:
        logger.error(f"Failed to track event: {e}")
        await db.rollback()
        return {"status": "error", "message": "Failed to track event"}


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def track_batch(
    events: list[AnalyticsEventPayload],
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    Track multiple analytics events in a single request (batch mode).
    
    More efficient for sending multiple events at once.
    """
    try:
        event_models = []
        for payload in events:
            enriched_properties = {
                **payload.properties,
                "user_agent": request.headers.get("user-agent", ""),
                "ip_address": request.client.host if request.client else None,
            }
            
            event = AnalyticsEvent(
                user_id=current_user.id if current_user else None,
                session_id=payload.session_id,
                event_name=payload.event_name,
                properties=enriched_properties,
                created_at=datetime.now(timezone.utc),
            )
            event_models.append(event)
        
        db.add_all(event_models)
        await db.commit()
        
        return {"status": "ok", "events_tracked": len(event_models)}
        
    except Exception as e:
        logger.error(f"Failed to track batch events: {e}")
        await db.rollback()
        return {"status": "error", "message": "Failed to track events"}
