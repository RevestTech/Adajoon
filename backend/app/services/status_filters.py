"""Shared status-filter construction for channel/radio search endpoints."""

from sqlalchemy import func, or_, select
from sqlalchemy.sql import ColumnElement

from app.models import UserVote


def apply_status_filters(
    query,
    count_query,
    *,
    model,
    item_type: str,
    statuses: list[str],
    has_stream_cond: ColumnElement,
    live_cond: ColumnElement,
):
    """Apply has_stream/verified/live/hide_offline/highly_rated status filters
    to both the data and count queries.

    `has_stream_cond` and `live_cond` are model-specific since "live" means
    something different for a TV channel (health_status in a set) than for a
    radio station (health_status OR last_check_ok).
    """
    health_includes = []
    for status in statuses:
        if status == "has_stream":
            query = query.where(has_stream_cond)
            count_query = count_query.where(has_stream_cond)
        elif status == "verified":
            health_includes.append(model.health_status == "verified")
        elif status == "live":
            health_includes.append(live_cond)
        elif status == "hide_offline":
            cond = ~model.health_status.in_(
                ("offline", "error", "timeout", "geo_blocked")
            )
            query = query.where(cond)
            count_query = count_query.where(cond)
        elif status == "highly_rated":
            subq = (
                select(UserVote.item_id)
                .where(
                    UserVote.item_type == item_type,
                    UserVote.vote_type.in_(("works", "like")),
                )
                .group_by(UserVote.item_id)
                .having(func.count(UserVote.id) >= 3)
            )
            query = query.where(model.id.in_(subq))
            count_query = count_query.where(model.id.in_(subq))

    if health_includes:
        combined = (
            health_includes[0] if len(health_includes) == 1 else or_(*health_includes)
        )
        query = query.where(combined)
        count_query = count_query.where(combined)

    return query, count_query
