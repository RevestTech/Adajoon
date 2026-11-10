"""
Admin-only API endpoints for dashboard overview/stats.

User/subscription management lives in admin_users.py, content moderation in
admin_content.py, and self-hosted analytics reporting in admin_analytics.py -
this file kept growing past 1,000 lines before that split.
"""

import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.admin_required import require_admin
from app.models import (
    AdminAuditLog,
    Channel,
    Playlist,
    RadioStation,
    User,
    UserFavorite,
    UserVote,
    WatchHistory,
)
from app.redis_client import health_check as redis_health_check
from app.services import settings_service

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)

# Kept in sync with the phase names in worker.py's run_cycle() - not
# imported from there to avoid coupling the API to the worker's logging
# setup for five string constants.
SYNC_PHASES = [
    "validate_all_channels",
    "validate_all_radio",
    "iptv_full_sync",
    "sync_radio_stations",
    "sync_epg",
]


@router.get("/stats/overview")
async def get_stats_overview(
    admin_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
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
        select(func.count(User.id)).where(User.last_login_at >= week_ago)
    )
    active_users_week = active_users_query.scalar() or 0

    # New signups in last 30 days
    month_ago = datetime.utcnow() - timedelta(days=30)
    new_users_query = await db.execute(
        select(func.count(User.id)).where(User.created_at >= month_ago)
    )
    new_users_month = new_users_query.scalar() or 0

    # Admin count
    admin_count_query = await db.execute(
        select(func.count(User.id)).where(User.is_admin.is_(True))
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
        select(func.count(WatchHistory.id)).where(WatchHistory.watched_at >= week_ago)
    )
    recent_watches = recent_watches_query.scalar() or 0

    # System health - db is implicitly healthy if we got this far (every
    # query above already required a working connection)
    redis_healthy = await redis_health_check()
    last_sync_at = await settings_service.get_setting(db, "last_sync_at")

    sync_phases = {}
    for phase in SYNC_PHASES:
        raw = await settings_service.get_setting(db, f"sync_phase:{phase}")
        sync_phases[phase] = json.loads(raw) if raw else None

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
            "db_healthy": True,
            "last_sync_at": last_sync_at,
            "sync_phases": sync_phases,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@router.get("/audit-log")
async def get_audit_log(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Reverse-chronological log of admin actions that changed state - see
    app/services/audit_service.py for what's logged and why."""
    result = await db.execute(
        select(AdminAuditLog)
        .order_by(AdminAuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.scalars().all()
    total = (await db.execute(select(func.count(AdminAuditLog.id)))).scalar() or 0
    return {
        "entries": [
            {
                "id": r.id,
                "admin_email": r.admin_email,
                "action": r.action,
                "target_type": r.target_type,
                "target_id": r.target_id,
                "detail": r.detail,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats/users")
async def get_user_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
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
            func.date(User.created_at).label("date"), func.count(User.id).label("count")
        )
        .where(User.created_at >= since)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    signups_by_day = [
        {"date": str(row.date), "count": row.count} for row in daily_signups
    ]

    # Users by provider
    by_provider = await db.execute(
        select(User.provider, func.count(User.id).label("count")).group_by(
            User.provider
        )
    )
    users_by_provider = [
        {"provider": row.provider, "count": row.count} for row in by_provider
    ]

    # Users by subscription tier
    by_tier = await db.execute(
        select(User.subscription_tier, func.count(User.id).label("count")).group_by(
            User.subscription_tier
        )
    )
    users_by_tier = [
        {"tier": row.subscription_tier or "free", "count": row.count} for row in by_tier
    ]

    # Top users by activity (most favorites)
    top_users = await db.execute(
        select(
            User.email,
            User.name,
            User.created_at,
            User.last_login_at,
            func.count(UserFavorite.id).label("favorites_count"),
        )
        .join(UserFavorite, User.id == UserFavorite.user_id, isouter=True)
        .group_by(User.id, User.email, User.name, User.created_at, User.last_login_at)
        .order_by(func.count(UserFavorite.id).desc())
        .limit(10)
    )
    most_active = [
        {
            "email": row.email,
            "name": row.name,
            "joined": row.created_at.isoformat() if row.created_at else None,
            "last_accessed": (
                row.last_login_at.isoformat() if row.last_login_at else None
            ),
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
    admin_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """
    Get content statistics.

    Includes most popular channels/stations and content health.
    """
    logger.info("Admin %s requested content stats", admin_user.email)

    # Most favorited TV channels
    top_tv = await db.execute(text("""
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
        """))
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
    top_radio = await db.execute(text("""
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
        """))
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
        select(Channel.health_status, func.count(Channel.id).label("count")).group_by(
            Channel.health_status
        )
    )
    channels_by_health = [
        {"status": row.health_status or "unknown", "count": row.count}
        for row in channel_health
    ]

    # Radio health status distribution
    radio_health = await db.execute(
        select(
            RadioStation.health_status, func.count(RadioStation.id).label("count")
        ).group_by(RadioStation.health_status)
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
    days: int = Query(default=30, ge=1, le=365),
):
    """
    Get user activity statistics.

    Includes watch history, voting patterns, and engagement metrics.
    """
    logger.info(
        "Admin %s requested activity stats (last %d days)", admin_user.email, days
    )

    since = datetime.utcnow() - timedelta(days=days)

    # Daily watch counts
    daily_watches = await db.execute(
        select(
            func.date(WatchHistory.watched_at).label("date"),
            WatchHistory.item_type,
            func.count(WatchHistory.id).label("count"),
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
            func.count(UserVote.id).label("count"),
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
            ).label("avg_items"),
        ).where(Playlist.created_at >= since)
    )
    playlist_row = playlist_stats.first()
    playlist_activity = {
        "created_this_period": playlist_row.created if playlist_row else 0,
        "avg_items_per_playlist": (
            float(playlist_row.avg_items)
            if playlist_row and playlist_row.avg_items
            else 0
        ),
    }

    return {
        "period_days": days,
        "watches_by_day": watches_by_day,
        "votes_breakdown": votes_breakdown,
        "playlist_activity": playlist_activity,
    }
