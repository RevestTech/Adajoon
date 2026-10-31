"""
Admin-only API endpoints for statistics and management.
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import Integer, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.csrf import verify_csrf_token
from app.database import get_db
from app.middleware.admin_required import require_admin
from app.models import (
    AnalyticsEvent,
    Channel,
    Playlist,
    PricingTier,
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


def _ilike_pattern(raw: str) -> str:
    """Escape ILIKE wildcard/escape characters in user input so a search for
    literal `%`, `_`, or `\\` doesn't act as a wildcard."""
    escaped = raw.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


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
            "timestamp": datetime.utcnow().isoformat(),
        },
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


@router.post("/users/{user_id}/make-admin")
async def make_user_admin(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
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
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
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


@router.get("/users")
async def list_users(
    q: str | None = Query(default=None, description="Search by email or name"),
    tier: str | None = Query(default=None),
    admin_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Search/list users for support and account management."""
    stmt = select(User)
    count_stmt = select(func.count(User.id))

    if q:
        pattern = _ilike_pattern(q)
        cond = or_(User.email.ilike(pattern), User.name.ilike(pattern))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    if tier:
        stmt = stmt.where(User.subscription_tier == tier)
        count_stmt = count_stmt.where(User.subscription_tier == tier)
    if admin_only:
        stmt = stmt.where(User.is_admin.is_(True))
        count_stmt = count_stmt.where(User.is_admin.is_(True))

    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = (
        stmt.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    users = (await db.execute(stmt)).scalars().all()

    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "is_admin": u.is_admin,
                "subscription_tier": u.subscription_tier,
                "subscription_status": u.subscription_status,
                "subscription_ends_at": (
                    u.subscription_ends_at.isoformat()
                    if u.subscription_ends_at
                    else None
                ),
                "stripe_customer_id": u.stripe_customer_id or "",
                "kids_mode_enabled": u.kids_mode_enabled,
                "has_parental_pin": bool(u.parental_pin_hash),
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login_at": (
                    u.last_login_at.isoformat() if u.last_login_at else None
                ),
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


class UserAdminUpdate(BaseModel):
    subscription_tier: str | None = None
    subscription_status: str | None = None
    subscription_ends_at: datetime | None = None
    clear_parental_pin: bool = False


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: int,
    payload: UserAdminUpdate,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    _csrf: None = Depends(verify_csrf_token),
):
    """Comp/revoke a subscription or clear a locked-out parental PIN.

    Writes directly to the User row rather than Stripe - for manual grants
    (press, partners, support goodwill) and support overrides, not for
    managing a real paid subscription (use the Stripe dashboard for that;
    the existing webhook handler keeps real subscriptions in sync with
    these same fields).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.subscription_tier is not None:
        if payload.subscription_tier != "free":
            tier_exists = (
                await db.execute(
                    select(PricingTier.key).where(
                        PricingTier.key == payload.subscription_tier
                    )
                )
            ).scalar_one_or_none()
            if not tier_exists:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown subscription_tier: {payload.subscription_tier!r}",
                )
        target.subscription_tier = payload.subscription_tier
    if payload.subscription_status is not None:
        target.subscription_status = payload.subscription_status
    if payload.subscription_ends_at is not None:
        target.subscription_ends_at = payload.subscription_ends_at
    if payload.clear_parental_pin:
        target.parental_pin_hash = ""
        target.kids_mode_enabled = False

    await db.commit()
    logger.info("Admin %s updated user %s", admin_user.email, target.email)
    return {"success": True}


@router.get("/subscriptions")
async def list_subscriptions(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Everyone with a non-free tier or a subscription status - comped
    accounts included. Stripe stays the source of truth for billing;
    this is a read view plus the comp/revoke actions on /users/{id}."""
    result = await db.execute(
        select(User)
        .where(or_(User.subscription_tier != "free", User.subscription_status != ""))
        .order_by(User.subscription_ends_at.desc().nulls_last())
    )
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "tier": u.subscription_tier,
            "status": u.subscription_status,
            "ends_at": (
                u.subscription_ends_at.isoformat() if u.subscription_ends_at else None
            ),
            "stripe_customer_id": u.stripe_customer_id or "",
        }
        for u in users
    ]


@router.get("/revenue")
async def get_revenue_summary(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Rough current MRR: active/comped subscribers per tier times that
    tier's current price. Not a Stripe reconciliation - just enough signal
    for a tiny team to see if the business is moving."""
    result = await db.execute(
        select(
            User.subscription_tier,
            func.count(User.id).label("count"),
        )
        .where(User.subscription_tier != "free")
        .where(User.subscription_status == "active")
        .group_by(User.subscription_tier)
    )
    counts_by_tier = {row.subscription_tier: row.count for row in result.all()}

    tiers_result = await db.execute(select(PricingTier))
    tiers = tiers_result.scalars().all()

    breakdown = []
    mrr_cents = 0
    for t in tiers:
        count = counts_by_tier.get(t.key, 0)
        tier_mrr_cents = count * t.monthly_price_cents
        mrr_cents += tier_mrr_cents
        if count:
            breakdown.append(
                {
                    "tier": t.key,
                    "subscribers": count,
                    "mrr": tier_mrr_cents / 100,
                }
            )

    return {"mrr": mrr_cents / 100, "breakdown": breakdown}


# ===========================================================================
# CONTENT MODERATION (hide a broken/inappropriate channel or station - the
# IPTV/radio sync jobs overwrite is_active/last_check_ok every run, so that
# can't be used as a manual override; admin_hidden is separate and sticky)
# ===========================================================================


@router.get("/channels/search")
async def admin_search_channels(
    q: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    pattern = _ilike_pattern(q)
    cond = Channel.name.ilike(pattern)
    total = (
        await db.execute(select(func.count(Channel.id)).where(cond))
    ).scalar() or 0
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
    cond = RadioStation.name.ilike(pattern)
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
    logger.info(
        "Admin %s set station %s admin_hidden=%s", admin_user.email, station_id, hidden
    )
    return {"success": True, "admin_hidden": hidden}


# ===========================================================================
# ANALYTICS ENDPOINTS
# ===========================================================================


@router.get("/analytics/summary")
async def get_analytics_summary(
    days: int = Query(default=7, ge=1, le=90),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics summary for the specified time period.

    Returns event counts, session stats, and top events.
    """
    logger.info(
        "Admin %s requested analytics summary for %d days", admin_user.email, days
    )

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Total events
    total_events_query = await db.execute(
        select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.created_at >= cutoff_date
        )
    )
    total_events = total_events_query.scalar() or 0

    # Unique sessions
    unique_sessions_query = await db.execute(
        select(func.count(func.distinct(AnalyticsEvent.session_id))).where(
            AnalyticsEvent.created_at >= cutoff_date
        )
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
        select(AnalyticsEvent.event_name, func.count(AnalyticsEvent.id).label("count"))
        .where(AnalyticsEvent.created_at >= cutoff_date)
        .group_by(AnalyticsEvent.event_name)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(10)
    )
    top_events = [
        {"event_name": row[0], "count": row[1]} for row in top_events_query.all()
    ]

    # Average session duration (from Session Ended events)
    avg_duration_query = await db.execute(
        select(
            func.avg(
                func.cast(
                    func.jsonb_extract_path_text(
                        AnalyticsEvent.properties, "total_duration_seconds"
                    ),
                    Integer,
                )
            )
        )
        .where(AnalyticsEvent.event_name == "Session Ended")
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
    db: AsyncSession = Depends(get_db),
):
    """
    Get event counts over time (daily breakdown).

    Optionally filter by specific event name.
    """
    logger.info(
        "Admin %s requested events over time for %d days", admin_user.email, days
    )

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    day_expr = func.date_trunc("day", AnalyticsEvent.created_at)
    query = select(
        day_expr.label("date"),
        func.count(AnalyticsEvent.id).label("count"),
    ).where(AnalyticsEvent.created_at >= cutoff_date)

    if event_name:
        query = query.where(AnalyticsEvent.event_name == event_name)

    query = query.group_by(day_expr).order_by(day_expr)

    result = await db.execute(query)

    return [
        {"date": row[0].date().isoformat(), "count": row[1]} for row in result.all()
    ]


@router.get("/analytics/auth-funnel")
async def get_auth_funnel(
    days: int = Query(default=7, ge=1, le=90),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get auth funnel breakdown: attempts, successes, failures, and lost sessions.

    Includes a per-method breakdown and the most recent login failures.
    """
    logger.info("Admin %s requested auth funnel for %d days", admin_user.email, days)

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    async def _count(event_names: list[str]) -> int:
        result = await db.execute(
            select(func.count(AnalyticsEvent.id))
            .where(AnalyticsEvent.event_name.in_(event_names))
            .where(AnalyticsEvent.created_at >= cutoff_date)
        )
        return result.scalar() or 0

    attempts = await _count(["Auth Login Attempted"])
    successes = await _count(["User Logged In", "User Signed Up"])
    failures = await _count(["Auth Login Failed"])
    session_lost = await _count(["Auth Session Lost"])

    method_expr = func.jsonb_extract_path_text(AnalyticsEvent.properties, "method")

    by_method_result = await db.execute(
        select(
            AnalyticsEvent.event_name,
            method_expr.label("method"),
            func.count(AnalyticsEvent.id).label("count"),
        )
        .where(
            AnalyticsEvent.event_name.in_(
                ["User Logged In", "User Signed Up", "Auth Login Failed"]
            )
        )
        .where(AnalyticsEvent.created_at >= cutoff_date)
        .group_by(AnalyticsEvent.event_name, method_expr)
    )
    by_method: dict[str, dict[str, int]] = {}
    for row in by_method_result.all():
        method = row.method or "unknown"
        bucket = by_method.setdefault(method, {"success": 0, "failure": 0})
        if row.event_name == "Auth Login Failed":
            bucket["failure"] += row.count
        else:
            bucket["success"] += row.count

    recent_failures_result = await db.execute(
        select(
            AnalyticsEvent.created_at,
            method_expr.label("method"),
            func.jsonb_extract_path_text(AnalyticsEvent.properties, "error").label(
                "error"
            ),
            AnalyticsEvent.session_id,
        )
        .where(AnalyticsEvent.event_name == "Auth Login Failed")
        .where(AnalyticsEvent.created_at >= cutoff_date)
        .order_by(AnalyticsEvent.created_at.desc())
        .limit(25)
    )
    recent_failures = [
        {
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "method": row.method or "unknown",
            "error": row.error,
            "session_id": row.session_id,
        }
        for row in recent_failures_result.all()
    ]

    return {
        "period_days": days,
        "attempts": attempts,
        "successes": successes,
        "failures": failures,
        "session_lost": session_lost,
        "by_method": [
            {
                "method": method,
                "success": counts["success"],
                "failure": counts["failure"],
            }
            for method, counts in sorted(by_method.items())
        ],
        "recent_failures": recent_failures,
    }


@router.get("/analytics/paths")
async def get_analytics_paths(
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=30, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user navigation path statistics: top screens, navigations, and pages.
    """
    logger.info(
        "Admin %s requested analytics paths for %d days", admin_user.email, days
    )

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    screen_expr = func.jsonb_extract_path_text(AnalyticsEvent.properties, "screen")
    top_screens_result = await db.execute(
        select(
            screen_expr.label("screen"), func.count(AnalyticsEvent.id).label("count")
        )
        .where(AnalyticsEvent.event_name == "Screen View")
        .where(AnalyticsEvent.created_at >= cutoff_date)
        .group_by(screen_expr)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(limit)
    )
    top_screens = [
        {"screen": row.screen or "unknown", "count": row.count}
        for row in top_screens_result.all()
    ]

    from_expr = func.jsonb_extract_path_text(AnalyticsEvent.properties, "from_screen")
    to_expr = func.jsonb_extract_path_text(AnalyticsEvent.properties, "to_screen")
    top_navigations_result = await db.execute(
        select(
            from_expr.label("from_screen"),
            to_expr.label("to_screen"),
            func.count(AnalyticsEvent.id).label("count"),
        )
        .where(AnalyticsEvent.event_name == "Navigation")
        .where(AnalyticsEvent.created_at >= cutoff_date)
        .group_by(from_expr, to_expr)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(limit)
    )
    top_navigations = [
        {
            "from_screen": row.from_screen or "unknown",
            "to_screen": row.to_screen or "unknown",
            "count": row.count,
        }
        for row in top_navigations_result.all()
    ]

    page_expr = func.jsonb_extract_path_text(AnalyticsEvent.properties, "page")
    top_pages_result = await db.execute(
        select(page_expr.label("page"), func.count(AnalyticsEvent.id).label("count"))
        .where(AnalyticsEvent.event_name == "Page View")
        .where(AnalyticsEvent.created_at >= cutoff_date)
        .where(page_expr.isnot(None))
        .group_by(page_expr)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(limit)
    )
    top_pages = [
        {"page": row.page, "count": row.count} for row in top_pages_result.all()
    ]

    return {
        "period_days": days,
        "top_screens": top_screens,
        "top_navigations": top_navigations,
        "top_pages": top_pages,
    }


@router.get("/analytics/top-content")
async def get_top_content(
    days: int = Query(default=7, ge=1, le=90),
    item_type: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get most popular content by playback count.

    Optionally filter by item_type ('tv' or 'radio').
    """
    logger.info("Admin %s requested top content for %d days", admin_user.email, days)

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Query for Playback Started events
    item_name_expr = func.jsonb_extract_path_text(
        AnalyticsEvent.properties, "item_name"
    )
    item_type_expr = func.jsonb_extract_path_text(
        AnalyticsEvent.properties, "item_type"
    )
    query = (
        select(
            item_name_expr.label("item_name"),
            item_type_expr.label("item_type"),
            func.count(AnalyticsEvent.id).label("play_count"),
        )
        .where(AnalyticsEvent.event_name == "Playback Started")
        .where(AnalyticsEvent.created_at >= cutoff_date)
    )

    if item_type:
        query = query.where(item_type_expr == item_type)

    query = (
        query.group_by(item_name_expr, item_type_expr)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(limit)
    )

    result = await db.execute(query)

    return [
        {"item_name": row[0], "item_type": row[1], "play_count": row[2]}
        for row in result.all()
    ]
