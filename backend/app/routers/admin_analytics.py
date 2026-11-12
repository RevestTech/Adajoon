"""Admin-only analytics/reporting endpoints (self-hosted event analytics)."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.admin_required import require_admin
from app.models import AnalyticsEvent, User

router = APIRouter(prefix="/api/admin/analytics", tags=["admin", "analytics"])
logger = logging.getLogger(__name__)


@router.get("/summary")
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


@router.get("/events-over-time")
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


@router.get("/auth-funnel")
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


@router.get("/paths")
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


@router.get("/top-content")
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


_AD_EVENT_NAMES = (
    "Ad Requested",
    "Ad Impression",
    "Ad Error",
    "Ad Completed",
    "Ad Skipped",
)


@router.get("/ads")
async def get_ad_performance(
    days: int = Query(default=7, ge=1, le=90),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Ad impression/fill-rate summary for the specified time period.

    Fill rate = impressions / requests (a request that doesn't become an
    impression means the ad server returned no fill, or the ad errored
    before it could render). Per-day trend for any one of these counts is
    already available via GET /events-over-time?event_name=<name>.
    """
    logger.info("Admin %s requested ad performance for %d days", admin_user.email, days)

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            AnalyticsEvent.event_name,
            func.count(AnalyticsEvent.id).label("count"),
        )
        .where(AnalyticsEvent.event_name.in_(_AD_EVENT_NAMES))
        .where(AnalyticsEvent.created_at >= cutoff_date)
        .group_by(AnalyticsEvent.event_name)
    )
    counts = {name: 0 for name in _AD_EVENT_NAMES}
    counts.update({row.event_name: row.count for row in result.all()})

    requested = counts["Ad Requested"]
    impressions = counts["Ad Impression"]
    fill_rate = round(impressions / requested, 4) if requested else None

    return {
        "period_days": days,
        "requested": requested,
        "impressions": impressions,
        "errors": counts["Ad Error"],
        "completed": counts["Ad Completed"],
        "skipped": counts["Ad Skipped"],
        "fill_rate": fill_rate,
    }
