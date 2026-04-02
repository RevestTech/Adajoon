from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Channel, Category, Country, Stream, RadioStation
from app.schemas import ChannelSearchParams


async def search_channels(db: AsyncSession, params: ChannelSearchParams):
    query = select(Channel).where(Channel.is_nsfw == False)
    count_query = select(func.count(Channel.id)).where(Channel.is_nsfw == False)

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
        health_includes = []
        for s in statuses:
            if s == "has_stream":
                query = query.where(Channel.stream_url != "")
                count_query = count_query.where(Channel.stream_url != "")
            elif s == "verified":
                health_includes.append(Channel.health_status == "verified")
            elif s == "live":
                health_includes.append(Channel.health_status.in_(("verified", "online", "manifest_only")))
            elif s == "hide_offline":
                cond = ~Channel.health_status.in_(("offline", "error", "timeout", "geo_blocked"))
                query = query.where(cond)
                count_query = count_query.where(cond)
        if health_includes:
            combined = health_includes[0] if len(health_includes) == 1 else or_(*health_includes)
            query = query.where(combined)
            count_query = count_query.where(combined)

    total = (await db.execute(count_query)).scalar() or 0

    offset = (params.page - 1) * params.per_page
    query = query.order_by(Channel.name).offset(offset).limit(params.per_page)

    result = await db.execute(query)
    channels = result.scalars().all()

    return channels, total


async def get_channel_by_id(db: AsyncSession, channel_id: str):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
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
        .outerjoin(Channel, (Channel.category_id == Category.id) & (Channel.is_nsfw == False))
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
        .outerjoin(Channel, (Channel.country_code == Country.code) & (Channel.is_nsfw == False))
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
