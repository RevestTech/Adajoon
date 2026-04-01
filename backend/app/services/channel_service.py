from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Channel, Category, Country, Stream
from app.schemas import ChannelSearchParams


async def search_channels(db: AsyncSession, params: ChannelSearchParams):
    query = select(Channel)
    count_query = select(func.count(Channel.id))

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
        query = query.where(Channel.categories.ilike(f"%{params.category}%"))
        count_query = count_query.where(Channel.categories.ilike(f"%{params.category}%"))

    if params.country:
        query = query.where(Channel.country_code == params.country)
        count_query = count_query.where(Channel.country_code == params.country)

    if params.language:
        query = query.where(Channel.languages.ilike(f"%{params.language}%"))
        count_query = count_query.where(Channel.languages.ilike(f"%{params.language}%"))

    if params.live_only:
        query = query.where(Channel.stream_url != "")
        count_query = count_query.where(Channel.stream_url != "")

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


async def get_categories_with_counts(db: AsyncSession):
    result = await db.execute(
        select(Category.id, Category.name, func.count(Channel.id).label("channel_count"))
        .outerjoin(Channel, Channel.category_id == Category.id)
        .group_by(Category.id, Category.name)
        .order_by(Category.name)
    )
    return result.all()


async def get_countries_with_counts(db: AsyncSession):
    result = await db.execute(
        select(Country.code, Country.name, Country.flag, func.count(Channel.id).label("channel_count"))
        .outerjoin(Channel, Channel.country_code == Country.code)
        .group_by(Country.code, Country.name, Country.flag)
        .having(func.count(Channel.id) > 0)
        .order_by(func.count(Channel.id).desc())
    )
    return result.all()


async def get_stats(db: AsyncSession):
    channels = (await db.execute(select(func.count(Channel.id)))).scalar() or 0
    categories = (await db.execute(select(func.count(Category.id)))).scalar() or 0
    countries = (await db.execute(select(func.count(Country.code)))).scalar() or 0
    streams = (await db.execute(select(func.count(Stream.id)))).scalar() or 0
    return {
        "total_channels": channels,
        "total_categories": categories,
        "total_countries": countries,
        "total_streams": streams,
    }
