"""
Admin-only API endpoints for statistics and management.
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, text, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    User, UserFavorite, UserVote, WatchHistory, 
    Playlist, Channel, RadioStation, AnalyticsEvent
)
from app.middleware.admin_required import require_admin
from app.redis_client import health_check as redis_health_check

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("/stats/overview")
async def get_stats_overview(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get high-level statistics overview.
    
    Returns user counts, content counts, and activity metrics.
    """
    logger.info("Admin %s requested stats overview", admin_user.email)
    
    # User statistics
    total_users_query = await db.execute(select(func.count(User.id)))
    total_users = total_users_query.scalar() or 0
    
    # Users in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users_query = await db.execute(
        select(func.count(User.id))
        .where(User.last_login_at >= week_ago)
    )
    active_users_week = active_users_query.scalar() or 0
    
    # New signups in last 30 days
    month_ago = datetime.utcnow() - timedelta(days=30)
    new_users_query = await db.execute(
        select(func.count(User.id))
        .where(User.created_at >= month_ago)
    )
    new_users_month = new_users_query.scalar() or 0
    
    # Admin count
    admin_count_query = await db.execute(
        select(func.count(User.id))
        .where(User.is_admin == True)
    )
    admin_count = admin_count_query.scalar() or 0
    
    # Subscription statistics
    paid_users_query = await db.execute(
        select(func.count(User.id))
        .where(User.subscription_tier != "free")
        .where(User.subscription_tier != "")
    )
    paid_users = paid_users_query.scalar() or 0
    
    # Content statistics
    total_channels_query = await db.execute(select(func.count(Channel.id)))
    total_channels = total_channels_query.scalar() or 0
    
    total_radio_query = await db.execute(select(func.count(RadioStation.id)))
    total_radio = total_radio_query.scalar() or 0
    
    # Activity statistics
    total_favorites_query = await db.execute(select(func.count(UserFavorite.id)))
    total_favorites = total_favorites_query.scalar() or 0
    
    total_votes_query = await db.execute(select(func.count(UserVote.id)))
    total_votes = total_votes_query.scalar() or 0
    
    total_playlists_query = await db.execute(select(func.count(Playlist.id)))
    total_playlists = total_playlists_query.scalar() or 0
    
    # Watch history in last 7 days
    recent_watches_query = await db.execute(
        select(func.count(WatchHistory.id))
        .where(WatchHistory.watched_at >= week_ago)
    )
    recent_watches = recent_watches_query.scalar() or 0
    
    # System health
    redis_healthy = await redis_health_check()
    
    return {
        "users": {
            "total": total_users,
            "active_this_week": active_users_week,
            "new_this_month": new_users_month,
            "admin_count": admin_count,
            "paid_users": paid_users,
        },
        "content": {
            "tv_channels": total_channels,
            "radio_stations": total_radio,
        },
        "activity": {
            "total_favorites": total_favorites,
            "total_votes": total_votes,
            "total_playlists": total_playlists,
            "watches_this_week": recent_watches,
        },
        "system": {
            "redis_healthy": redis_healthy,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }


@router.get("/stats/users")
async def get_user_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get detailed user statistics.
    
    Includes signup trends, login activity, and subscription breakdown.
    """
    logger.info("Admin %s requested user stats (last %d days)", admin_user.email, days)
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Daily signups
    daily_signups = await db.execute(
        select(
            func.date(User.created_at).label("date"),
            func.count(User.id).label("count")
        )
        .where(User.created_at >= since)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    signups_by_day = [
        {"date": str(row.date), "count": row.count}
        for row in daily_signups
    ]
    
    # Users by provider
    by_provider = await db.execute(
        select(
            User.provider,
            func.count(User.id).label("count")
        )
        .group_by(User.provider)
    )
    users_by_provider = [
        {"provider": row.provider, "count": row.count}
        for row in by_provider
    ]
    
    # Users by subscription tier
    by_tier = await db.execute(
        select(
            User.subscription_tier,
            func.count(User.id).label("count")
        )
        .group_by(User.subscription_tier)
    )
    users_by_tier = [
        {"tier": row.subscription_tier or "free", "count": row.count}
        for row in by_tier
    ]
    
    # Top users by activity (most favorites)
    top_users = await db.execute(
        select(
            User.email,
            User.name,
            User.created_at,
            func.count(UserFavorite.id).label("favorites_count")
        )
        .join(UserFavorite, User.id == UserFavorite.user_id, isouter=True)
        .group_by(User.id, User.email, User.name, User.created_at)
        .order_by(func.count(UserFavorite.id).desc())
        .limit(10)
    )
    most_active = [
        {
            "email": row.email,
            "name": row.name,
            "joined": row.created_at.isoformat() if row.created_at else None,
            "favorites_count": row.favorites_count,
        }
        for row in top_users
    ]
    
    return {
        "period_days": days,
        "signups_by_day": signups_by_day,
        "users_by_provider": users_by_provider,
        "users_by_tier": users_by_tier,
        "most_active_users": most_active,
    }


@router.get("/stats/content")
async def get_content_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get content statistics.
    
    Includes most popular channels/stations and content health.
    """
    logger.info("Admin %s requested content stats", admin_user.email)
    
    # Most favorited TV channels
    top_tv = await db.execute(
        text("""
            SELECT 
                uf.item_id,
                COUNT(*) as favorites_count,
                MAX(uf.item_data::json->>'name') as name,
                MAX(uf.item_data::json->>'logo') as logo
            FROM user_favorites uf
            WHERE uf.item_type = 'tv'
            GROUP BY uf.item_id
            ORDER BY favorites_count DESC
            LIMIT 10
        """)
    )
    most_favorited_tv = [
        {
            "id": row.item_id,
            "name": row.name,
            "logo": row.logo,
            "favorites": row.favorites_count,
        }
        for row in top_tv
    ]
    
    # Most favorited radio stations
    top_radio = await db.execute(
        text("""
            SELECT 
                uf.item_id,
                COUNT(*) as favorites_count,
                MAX(uf.item_data::json->>'name') as name,
                MAX(uf.item_data::json->>'favicon') as favicon
            FROM user_favorites uf
            WHERE uf.item_type = 'radio'
            GROUP BY uf.item_id
            ORDER BY favorites_count DESC
            LIMIT 10
        """)
    )
    most_favorited_radio = [
        {
            "id": row.item_id,
            "name": row.name,
            "favicon": row.favicon,
            "favorites": row.favorites_count,
        }
        for row in top_radio
    ]
    
    # Channel health status distribution
    channel_health = await db.execute(
        select(
            Channel.health_status,
            func.count(Channel.id).label("count")
        )
        .group_by(Channel.health_status)
    )
    channels_by_health = [
        {"status": row.health_status or "unknown", "count": row.count}
        for row in channel_health
    ]
    
    # Radio health status distribution
    radio_health = await db.execute(
        select(
            RadioStation.health_status,
            func.count(RadioStation.id).label("count")
        )
        .group_by(RadioStation.health_status)
    )
    radio_by_health = [
        {"status": row.health_status or "unknown", "count": row.count}
        for row in radio_health
    ]
    
    return {
        "most_favorited_tv": most_favorited_tv,
        "most_favorited_radio": most_favorited_radio,
        "channels_by_health": channels_by_health,
        "radio_by_health": radio_by_health,
    }


@router.get("/stats/activity")
async def get_activity_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get user activity statistics.
    
    Includes watch history, voting patterns, and engagement metrics.
    """
    logger.info("Admin %s requested activity stats (last %d days)", admin_user.email, days)
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Daily watch counts
    daily_watches = await db.execute(
        select(
            func.date(WatchHistory.watched_at).label("date"),
            WatchHistory.item_type,
            func.count(WatchHistory.id).label("count")
        )
        .where(WatchHistory.watched_at >= since)
        .group_by(func.date(WatchHistory.watched_at), WatchHistory.item_type)
        .order_by(func.date(WatchHistory.watched_at))
    )
    watches_by_day = [
        {"date": str(row.date), "type": row.item_type, "count": row.count}
        for row in daily_watches
    ]
    
    # Vote distribution
    vote_distribution = await db.execute(
        select(
            UserVote.vote_type,
            UserVote.item_type,
            func.count(UserVote.id).label("count")
        )
        .where(UserVote.created_at >= since)
        .group_by(UserVote.vote_type, UserVote.item_type)
    )
    votes_breakdown = [
        {"vote_type": row.vote_type, "item_type": row.item_type, "count": row.count}
        for row in vote_distribution
    ]
    
    # Playlist activity
    playlist_stats = await db.execute(
        select(
            func.count(Playlist.id).label("created"),
            func.avg(
                select(func.count())
                .select_from(text("playlist_items"))
                .where(text("playlist_items.playlist_id = playlists.id"))
                .scalar_subquery()
            ).label("avg_items")
        )
        .where(Playlist.created_at >= since)
    )
    playlist_row = playlist_stats.first()
    playlist_activity = {
        "created_this_period": playlist_row.created if playlist_row else 0,
        "avg_items_per_playlist": float(playlist_row.avg_items) if playlist_row and playlist_row.avg_items else 0,
    }
    
    return {
        "period_days": days,
        "watches_by_day": watches_by_day,
        "votes_breakdown": votes_breakdown,
        "playlist_activity": playlist_activity,
    }


@router.post("/users/{user_id}/make-admin")
async def make_user_admin(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Grant admin privileges to a user.
    
    Requires admin access.
    """
    logger.info("Admin %s granting admin to user ID %d", admin_user.email, user_id)
    
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        return {"error": "User not found"}
    
    target_user.is_admin = True
    target_user.role = "admin"
    await db.commit()
    
    logger.info("User %s is now an admin", target_user.email)
    
    return {
        "success": True,
        "user_id": user_id,
        "email": target_user.email,
        "is_admin": True,
    }


@router.post("/users/{user_id}/revoke-admin")
async def revoke_user_admin(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke admin privileges from a user.
    
    Requires admin access.
    """
    logger.info("Admin %s revoking admin from user ID %d", admin_user.email, user_id)
    
    # Prevent self-demotion
    if admin_user.id == user_id:
        return {"error": "Cannot revoke your own admin privileges"}
    
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        return {"error": "User not found"}
    
    target_user.is_admin = False
    target_user.role = "user"
    await db.commit()
    
    logger.info("Admin privileges revoked for user %s", target_user.email)
    
    return {
        "success": True,
        "user_id": user_id,
        "email": target_user.email,
        "is_admin": False,
    }


# ===========================================================================
# ANALYTICS ENDPOINTS
# ===========================================================================

@router.get("/analytics/summary")
async def get_analytics_summary(
    days: int = Query(default=7, ge=1, le=90),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics summary for the specified time period.
    
    Returns event counts, session stats, and top events.
    """
    logger.info("Admin %s requested analytics summary for %d days", admin_user.email, days)
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total events
    total_events_query = await db.execute(
        select(func.count(AnalyticsEvent.id))
        .where(AnalyticsEvent.created_at >= cutoff_date)
    )
    total_events = total_events_query.scalar() or 0
    
    # Unique sessions
    unique_sessions_query = await db.execute(
        select(func.count(func.distinct(AnalyticsEvent.session_id)))
        .where(AnalyticsEvent.created_at >= cutoff_date)
    )
    unique_sessions = unique_sessions_query.scalar() or 0
    
    # Unique users
    unique_users_query = await db.execute(
        select(func.count(func.distinct(AnalyticsEvent.user_id)))
        .where(AnalyticsEvent.created_at >= cutoff_date)
        .where(AnalyticsEvent.user_id.isnot(None))
    )
    unique_users = unique_users_query.scalar() or 0
    
    # Top events
    top_events_query = await db.execute(
        select(
            AnalyticsEvent.event_name,
            func.count(AnalyticsEvent.id).label('count')
        )
        .where(AnalyticsEvent.created_at >= cutoff_date)
        .group_by(AnalyticsEvent.event_name)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(10)
    )
    top_events = [
        {"event_name": row[0], "count": row[1]}
        for row in top_events_query.all()
    ]
    
    # Average session duration (from Session Ended events)
    avg_duration_query = await db.execute(
        select(func.avg(
            func.cast(
                func.jsonb_extract_path_text(AnalyticsEvent.properties, 'total_duration_seconds'),
                Integer
            )
        ))
        .where(AnalyticsEvent.event_name == 'Session Ended')
        .where(AnalyticsEvent.created_at >= cutoff_date)
    )
    avg_session_duration = avg_duration_query.scalar() or 0
    
    return {
        "period_days": days,
        "total_events": total_events,
        "unique_sessions": unique_sessions,
        "unique_users": unique_users,
        "avg_session_duration_seconds": int(avg_session_duration),
        "top_events": top_events,
    }


@router.get("/analytics/events-over-time")
async def get_events_over_time(
    days: int = Query(default=7, ge=1, le=90),
    event_name: str | None = Query(default=None),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get event counts over time (daily breakdown).
    
    Optionally filter by specific event name.
    """
    logger.info("Admin %s requested events over time for %d days", admin_user.email, days)
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(
        func.date_trunc('day', AnalyticsEvent.created_at).label('date'),
        func.count(AnalyticsEvent.id).label('count')
    ).where(AnalyticsEvent.created_at >= cutoff_date)
    
    if event_name:
        query = query.where(AnalyticsEvent.event_name == event_name)
    
    query = query.group_by(func.date_trunc('day', AnalyticsEvent.created_at)) \
                 .order_by(func.date_trunc('day', AnalyticsEvent.created_at))
    
    result = await db.execute(query)
    
    return [
        {
            "date": row[0].date().isoformat(),
            "count": row[1]
        }
        for row in result.all()
    ]


@router.get("/analytics/top-content")
async def get_top_content(
    days: int = Query(default=7, ge=1, le=90),
    item_type: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get most popular content by playback count.
    
    Optionally filter by item_type ('tv' or 'radio').
    """
    logger.info("Admin %s requested top content for %d days", admin_user.email, days)
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Query for Playback Started events
    query = select(
        func.jsonb_extract_path_text(AnalyticsEvent.properties, 'item_name').label('item_name'),
        func.jsonb_extract_path_text(AnalyticsEvent.properties, 'item_type').label('item_type'),
        func.count(AnalyticsEvent.id).label('play_count')
    ).where(AnalyticsEvent.event_name == 'Playback Started') \
     .where(AnalyticsEvent.created_at >= cutoff_date)
    
    if item_type:
        query = query.where(
            func.jsonb_extract_path_text(AnalyticsEvent.properties, 'item_type') == item_type
        )
    
    query = query.group_by(
        func.jsonb_extract_path_text(AnalyticsEvent.properties, 'item_name'),
        func.jsonb_extract_path_text(AnalyticsEvent.properties, 'item_type')
    ).order_by(func.count(AnalyticsEvent.id).desc()) \
     .limit(limit)
    
    result = await db.execute(query)
    
    return [
        {
            "item_name": row[0],
            "item_type": row[1],
            "play_count": row[2]
        }
        for row in result.all()
    ]
