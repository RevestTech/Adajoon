"""Recommendation endpoints."""

from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Channel, RadioStation, UserVote
from app.redis_client import cache_get, cache_set

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])
limiter = Limiter(key_func=get_remote_address)

CACHE_TTL = 300
POSITIVE_VOTE_TYPES = ("like", "works")
NEGATIVE_VOTE_TYPES = ("dislike", "broken")


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
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
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
        *(
            [
                func.strpos(Channel.categories, cat)
                for cat in (source.categories or "").split(";")
                if cat.strip()
            ]
            if source.categories
            else [0]
        )
    )

    country_match = (Channel.country_code == source.country_code).cast(Integer)

    # Channels have no vote columns of their own - votes live in UserVote.
    positive_votes = (
        select(func.count(UserVote.id))
        .where(
            UserVote.item_type == "tv",
            UserVote.item_id == Channel.id,
            UserVote.vote_type.in_(POSITIVE_VOTE_TYPES),
        )
        .correlate(Channel)
        .scalar_subquery()
    )
    negative_votes = (
        select(func.count(UserVote.id))
        .where(
            UserVote.item_type == "tv",
            UserVote.item_id == Channel.id,
            UserVote.vote_type.in_(NEGATIVE_VOTE_TYPES),
        )
        .correlate(Channel)
        .scalar_subquery()
    )

    score = (
        category_match * 10  # Category match is most important
        + country_match * 5  # Country match is secondary
        + positive_votes * 0.1  # Positive votes help
        - negative_votes * 0.05  # Negative votes hurt
        + (Channel.health_status == "verified").cast(Integer) * 2
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
            "country": ch.country_code,
            "categories": ch.categories,
            "health_status": ch.health_status,
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
    result = await db.execute(select(RadioStation).where(RadioStation.id == station_id))
    source = result.scalar_one_or_none()
    if not source:
        return []

    # Build scoring query - similar to channels
    tag_match = func.greatest(
        *(
            [
                func.strpos(RadioStation.tags, tag)
                for tag in (source.tags or "").split(",")
                if tag.strip()
            ]
            if source.tags
            else [0]
        )
    )

    country_match = (RadioStation.country_code == source.country_code).cast(Integer)

    # RadioStation only carries a single external popularity counter
    # (synced from Radio Browser), not a split up/down vote pair.
    score = (
        tag_match * 10
        + country_match * 5
        + func.coalesce(RadioStation.votes, 0) * 0.05
        + (RadioStation.health_status == "verified").cast(Integer) * 2
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
            "votes": st.votes or 0,
        }
        for st in recommendations
    ]


@router.post("/similar")
@limiter.limit("30/minute")
async def get_recommendations(
    request: Request,
    params: RecommendationParams,
    db: AsyncSession = Depends(get_db),
):
    """Get recommendations similar to a channel or station."""
    cache_key = f"recommendations:{params.item_type}:{params.item_id}:{params.limit}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

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

    response = {
        "item_type": params.item_type,
        "item_id": params.item_id,
        "recommendations": recommendations,
    }
    await cache_set(cache_key, response, CACHE_TTL)
    return response
