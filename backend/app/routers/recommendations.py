"""Recommendation endpoints."""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models import Channel, RadioStation

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class RecommendationParams(BaseModel):
    item_type: Literal["tv", "radio"]
    item_id: str
    limit: int = 10


async def _get_channel_recommendations(
    channel_id: str,
    db: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    """Get recommendations for a TV channel."""
    # Get the source channel
    result = await db.execute(
        select(Channel).where(Channel.id == channel_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        return []
    
    # Build scoring query - prioritize:
    # 1. Same category (high weight)
    # 2. Same country (medium weight)
    # 3. High upvotes (medium weight)
    # 4. Low downvotes (low weight)
    # 5. Verified/online status (bonus)
    
    category_match = func.greatest(
        *[
            func.position(cat, Channel.categories)
            for cat in (source.categories or "").split(",")
            if cat.strip()
        ]
        if source.categories else [0]
    )
    
    country_match = (Channel.country == source.country).cast(db.bind.dialect.INT)
    
    score = (
        category_match * 10 +  # Category match is most important
        country_match * 5 +     # Country match is secondary
        func.coalesce(Channel.upvotes, 0) * 0.1 -  # Positive votes help
        func.coalesce(Channel.downvotes, 0) * 0.05 +  # Negative votes hurt
        (Channel.health_status == "verified").cast(db.bind.dialect.INT) * 2
    )
    
    # Exclude source channel and get top recommendations
    result = await db.execute(
        select(Channel)
        .where(Channel.id != channel_id)
        .where(Channel.health_status.in_(["verified", "online"]))
        .order_by(score.desc())
        .limit(limit)
    )
    
    recommendations = result.scalars().all()
    
    return [
        {
            "id": ch.id,
            "name": ch.name,
            "logo": ch.logo,
            "country": ch.country,
            "categories": ch.categories,
            "health_status": ch.health_status,
            "upvotes": ch.upvotes or 0,
            "downvotes": ch.downvotes or 0,
        }
        for ch in recommendations
    ]


async def _get_station_recommendations(
    station_id: str,
    db: AsyncSession,
    limit: int = 10,
) -> list[dict]:
    """Get recommendations for a radio station."""
    # Get the source station
    result = await db.execute(
        select(RadioStation).where(RadioStation.id == station_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        return []
    
    # Build scoring query - similar to channels
    tag_match = func.greatest(
        *[
            func.position(tag, RadioStation.tags)
            for tag in (source.tags or "").split(",")
            if tag.strip()
        ]
        if source.tags else [0]
    )
    
    country_match = (RadioStation.country == source.country).cast(db.bind.dialect.INT)
    
    score = (
        tag_match * 10 +
        country_match * 5 +
        func.coalesce(RadioStation.upvotes, 0) * 0.1 -
        func.coalesce(RadioStation.downvotes, 0) * 0.05 +
        (RadioStation.health_status == "verified").cast(db.bind.dialect.INT) * 2
    )
    
    # Exclude source and get recommendations
    result = await db.execute(
        select(RadioStation)
        .where(RadioStation.id != station_id)
        .where(RadioStation.health_status.in_(["verified", "online"]))
        .order_by(score.desc())
        .limit(limit)
    )
    
    recommendations = result.scalars().all()
    
    return [
        {
            "id": st.id,
            "name": st.name,
            "favicon": st.favicon,
            "country": st.country,
            "tags": st.tags,
            "health_status": st.health_status,
            "upvotes": st.upvotes or 0,
            "downvotes": st.downvotes or 0,
        }
        for st in recommendations
    ]


@router.post("/similar")
async def get_recommendations(
    params: RecommendationParams,
    db: AsyncSession = Depends(get_db),
):
    """Get recommendations similar to a channel or station."""
    if params.item_type == "tv":
        recommendations = await _get_channel_recommendations(
            params.item_id,
            db,
            params.limit,
        )
    else:
        recommendations = await _get_station_recommendations(
            params.item_id,
            db,
            params.limit,
        )
    
    return {
        "item_type": params.item_type,
        "item_id": params.item_id,
        "recommendations": recommendations,
    }
