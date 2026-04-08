"""AI-powered natural language search endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.ai_search_service import ai_search_channels, ai_search_radio

router = APIRouter(prefix="/api/search", tags=["ai-search"])


class AISearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="Natural language search query")
    mode: str = Field("tv", pattern="^(tv|radio)$", description="Search mode: tv or radio")


@router.post("/ai")
async def ai_search(
    body: AISearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    AI-powered natural language search for channels or radio stations.

    Uses Claude to understand intent and find matching content.
    Falls back to smart keyword matching if AI is unavailable.
    """
    if not settings.ai_search_enabled:
        raise HTTPException(status_code=503, detail="AI search is currently disabled")

    if body.mode == "tv":
        return await ai_search_channels(db, body.query)
    else:
        return await ai_search_radio(db, body.query)


@router.get("/ai/status")
async def ai_search_status():
    """Check if AI search is available."""
    return {
        "enabled": settings.ai_search_enabled,
        "has_api_key": bool(settings.anthropic_api_key),
        "model": settings.ai_model if settings.anthropic_api_key else None,
    }
