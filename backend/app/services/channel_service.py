import re

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnalyticsEvent, Category, Channel, Country, Stream
from app.schemas import ChannelSearchParams
from app.services.status_filters import apply_status_filters

FOR_YOU_LOOKBACK_EVENTS = 50
FOR_YOU_DEFAULT_LIMIT = 10
FOR_YOU_MAX_LIMIT = 20


async def search_channels(db: AsyncSession, params: ChannelSearchParams):
    query = select(Channel).where(
        Channel.is_nsfw.is_(False), Channel.admin_hidden.is_(False)
    )
    count_query = select(func.count(Channel.id)).where(
        Channel.is_nsfw.is_(False), Channel.admin_hidden.is_(False)
    )

    if params.query:
        pattern = f"%{params.query}%"
        filter_cond = or_(
            Channel.name.ilike(pattern),
            Channel.alt_names.ilike(pattern),
            Channel.network.ilike(pattern),
        )
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    if params.category:
        cats = [c.strip() for c in params.category.split(",") if c.strip()]
        if len(cats) == 1:
            cond = Channel.categories.ilike(f"%{cats[0]}%")
        else:
            cond = or_(*[Channel.categories.ilike(f"%{c}%") for c in cats])
        query = query.where(cond)
        count_query = count_query.where(cond)

    if params.country:
        codes = [c.strip() for c in params.country.split(",") if c.strip()]
        if len(codes) == 1:
            cond = Channel.country_code == codes[0]
        else:
            cond = Channel.country_code.in_(codes)
        query = query.where(cond)
        count_query = count_query.where(cond)

    if params.language:
        query = query.where(Channel.languages.ilike(f"%{params.language}%"))
        count_query = count_query.where(Channel.languages.ilike(f"%{params.language}%"))

    if params.live_only:
        query = query.where(Channel.stream_url != "")
        count_query = count_query.where(Channel.stream_url != "")

    statuses = [s.strip() for s in (params.status or "").split(",") if s.strip()]
    if statuses:
        query, count_query = apply_status_filters(
            query,
            count_query,
            model=Channel,
            item_type="tv",
            statuses=statuses,
            has_stream_cond=(Channel.stream_url != ""),
            live_cond=Channel.health_status.in_(
                ("verified", "online", "manifest_only")
            ),
        )

    total = (await db.execute(count_query)).scalar() or 0

    offset = (params.page - 1) * params.per_page
    if params.query:
        # Rank by match quality so an exact/prefix name match (e.g. "BBC")
        # outranks a channel that only matches via a substring in its name,
        # alt_names, or network. Verified/online channels break ties, as a
        # cheap popularity proxy since there's no per-channel vote count to
        # join against without a much heavier query.
        q = params.query
        match_rank = case(
            (Channel.name.ilike(q), 0),
            (Channel.name.ilike(f"{q}%"), 1),
            (Channel.name.ilike(f"%{q}%"), 2),
            else_=3,
        )
        verified_rank = case(
            (Channel.health_status.in_(("verified", "online", "manifest_only")), 0),
            else_=1,
        )
        query = query.order_by(match_rank, verified_rank, Channel.name)
    else:
        query = query.order_by(Channel.name)
    query = query.offset(offset).limit(params.per_page)

    result = await db.execute(query)
    channels = result.scalars().all()

    return channels, total


async def get_for_you_channels(
    db: AsyncSession, session_id: str, limit: int = FOR_YOU_DEFAULT_LIMIT
) -> tuple[list[Channel], str | None]:
    """Channels in the category this browser session has watched the most,
    for a "For You" row - no login required. Reuses the existing "Content
    Played" analytics events already logged for every play (guest or not)
    instead of a new tracking table. Returns ([], None) once there's no
    play history yet for this session."""
    if not session_id:
        return [], None
    limit = max(1, min(limit, FOR_YOU_MAX_LIMIT))

    stmt = (
        select(AnalyticsEvent.properties)
        .where(
            AnalyticsEvent.session_id == session_id,
            AnalyticsEvent.event_name == "Content Played",
        )
        .order_by(AnalyticsEvent.created_at.desc())
        .limit(FOR_YOU_LOOKBACK_EVENTS)
    )
    result = await db.execute(stmt)

    played_ids: set[str] = set()
    category_counts: dict[str, int] = {}
    for (props,) in result:
        if not props or props.get("item_type") != "tv":
            continue
        item_id = props.get("item_id")
        if isinstance(item_id, str) and item_id:
            played_ids.add(item_id)
        item_category = props.get("item_category")
        if not isinstance(item_category, str):
            continue
        for cat in re.split(r"[;,]", item_category):
            cat = cat.strip()
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1

    if not category_counts:
        return [], None

    top_category = max(category_counts, key=category_counts.get)

    filters = [
        Channel.is_nsfw.is_(False),
        Channel.stream_url != "",
        Channel.categories.ilike(f"%{top_category}%"),
    ]
    if played_ids:
        filters.append(Channel.id.notin_(played_ids))

    stmt = select(Channel).where(*filters).order_by(func.random()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all()), top_category


async def get_channel_by_id(db: AsyncSession, channel_id: str):
    result = await db.execute(
        select(Channel).where(Channel.id == channel_id, Channel.admin_hidden.is_(False))
    )
    return result.scalar_one_or_none()


async def get_channel_streams(db: AsyncSession, channel_id: str):
    result = await db.execute(
        select(Stream).where(Stream.channel_id == channel_id).order_by(Stream.id)
    )
    return result.scalars().all()


_HIDDEN_CATEGORIES = {"xxx"}

# Matches TV filter chips: "live" = playable stream signal; "verified" = fully verified probe.
_LIVE_STATUSES = ("verified", "online", "manifest_only")


async def get_categories_with_counts(db: AsyncSession):
    live_cond = Channel.health_status.in_(_LIVE_STATUSES)
    verified_cond = Channel.health_status == "verified"
    result = await db.execute(
        select(
            Category.id,
            Category.name,
            func.count(Channel.id).label("channel_count"),
            func.count(case((live_cond, Channel.id))).label("live_count"),
            func.count(case((verified_cond, Channel.id))).label("verified_count"),
        )
        .outerjoin(
            Channel, (Channel.category_id == Category.id) & (Channel.is_nsfw.is_(False))
        )
        .where(~func.lower(Category.id).in_(_HIDDEN_CATEGORIES))
        .group_by(Category.id, Category.name)
        .order_by(Category.name)
    )
    return result.all()


async def get_countries_with_counts(db: AsyncSession):
    live_cond = Channel.health_status.in_(_LIVE_STATUSES)
    verified_cond = Channel.health_status == "verified"
    result = await db.execute(
        select(
            Country.code,
            Country.name,
            Country.flag,
            func.count(Channel.id).label("channel_count"),
            func.count(case((live_cond, Channel.id))).label("live_count"),
            func.count(case((verified_cond, Channel.id))).label("verified_count"),
        )
        .outerjoin(
            Channel,
            (Channel.country_code == Country.code) & (Channel.is_nsfw.is_(False)),
        )
        .group_by(Country.code, Country.name, Country.flag)
        .having(func.count(Channel.id) > 0)
        .order_by(func.count(Channel.id).desc())
    )
    return result.all()


async def get_stats(db: AsyncSession):
    from sqlalchemy import text

    row = (await db.execute(text("""
        SELECT
            (SELECT count(*) FROM channels WHERE is_nsfw = false) AS ch,
            (SELECT count(*) FROM categories WHERE lower(id) != 'xxx') AS cat,
            (SELECT count(*) FROM countries) AS co,
            (SELECT count(*) FROM streams) AS st,
            (SELECT count(*) FROM radio_stations) AS rs
    """))).one()
    return {
        "total_channels": row[0],
        "total_categories": row[1],
        "total_countries": row[2],
        "total_streams": row[3],
        "total_radio_stations": row[4],
    }
