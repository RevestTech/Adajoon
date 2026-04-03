import logging

import httpx
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models import RadioStation
from app.schemas import RadioSearchParams

logger = logging.getLogger(__name__)

RADIO_API = "https://de1.api.radio-browser.info"


async def fetch_radio_json(path: str, params: dict | None = None) -> list[dict]:
    async with httpx.AsyncClient(timeout=60, headers={"User-Agent": "Adajoon/1.0"}) as client:
        resp = await client.get(f"{RADIO_API}{path}", params=params)
        resp.raise_for_status()
        return resp.json()


async def sync_radio_stations(db: AsyncSession) -> int:
    """Fetch top radio stations from Radio Browser API with batched inserts."""
    logger.info("Starting radio station sync...")
    count = 0
    batch_size = 10000
    offset = 0
    max_stations = 50000
    insert_batch_size = 500

    while offset < max_stations:
        data = await fetch_radio_json("/json/stations/search", {
            "limit": batch_size,
            "offset": offset,
            "order": "votes",
            "reverse": "true",
            "hidebroken": "true",
        })

        if not data:
            break

        # Prepare batch of values for bulk insert
        values_batch = []
        for item in data:
            station_id = item.get("stationuuid", "")
            if not station_id:
                continue

            values_batch.append({
                "id": station_id,
                "name": item.get("name", "").strip(),
                "url": item.get("url", ""),
                "url_resolved": item.get("url_resolved", ""),
                "homepage": item.get("homepage", ""),
                "favicon": item.get("favicon", ""),
                "tags": item.get("tags", ""),
                "country": item.get("country", ""),
                "country_code": (item.get("countrycode", "") or "").upper(),
                "state": item.get("state", ""),
                "language": item.get("language", ""),
                "codec": item.get("codec", ""),
                "bitrate": item.get("bitrate", 0) or 0,
                "votes": item.get("votes", 0) or 0,
                "last_check_ok": bool(item.get("lastcheckok", 0)),
            })

        # Process in smaller chunks to avoid huge single statements
        for i in range(0, len(values_batch), insert_batch_size):
            chunk = values_batch[i:i + insert_batch_size]
            if not chunk:
                continue
                
            stmt = pg_insert(RadioStation).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": stmt.excluded.name,
                    "url": stmt.excluded.url,
                    "url_resolved": stmt.excluded.url_resolved,
                    "homepage": stmt.excluded.homepage,
                    "favicon": stmt.excluded.favicon,
                    "tags": stmt.excluded.tags,
                    "country": stmt.excluded.country,
                    "country_code": stmt.excluded.country_code,
                    "state": stmt.excluded.state,
                    "language": stmt.excluded.language,
                    "codec": stmt.excluded.codec,
                    "bitrate": stmt.excluded.bitrate,
                    "votes": stmt.excluded.votes,
                    "last_check_ok": stmt.excluded.last_check_ok,
                },
            )
            await db.execute(stmt)
            count += len(chunk)

        await db.commit()
        logger.info("Synced radio batch: offset=%d, got=%d, total=%d", offset, len(data), count)
        offset += batch_size

        if len(data) < batch_size:
            break

    logger.info("Radio sync complete: %d stations", count)
    return count


async def search_radio(db: AsyncSession, params: RadioSearchParams):
    query = select(RadioStation)
    count_query = select(func.count(RadioStation.id))

    if params.query:
        pattern = f"%{params.query}%"
        cond = or_(
            RadioStation.name.ilike(pattern),
            RadioStation.tags.ilike(pattern),
        )
        query = query.where(cond)
        count_query = count_query.where(cond)

    if params.tag:
        tags = [t.strip() for t in params.tag.split(",") if t.strip()]
        if len(tags) == 1:
            cond = RadioStation.tags.ilike(f"%{tags[0]}%")
        else:
            cond = or_(*[RadioStation.tags.ilike(f"%{t}%") for t in tags])
        query = query.where(cond)
        count_query = count_query.where(cond)

    if params.country:
        codes = [c.strip().upper() for c in params.country.split(",") if c.strip()]
        if len(codes) == 1:
            cond = RadioStation.country_code == codes[0]
        else:
            cond = RadioStation.country_code.in_(codes)
        query = query.where(cond)
        count_query = count_query.where(cond)

    if params.language:
        query = query.where(RadioStation.language.ilike(f"%{params.language}%"))
        count_query = count_query.where(RadioStation.language.ilike(f"%{params.language}%"))

    if params.working_only:
        query = query.where(RadioStation.last_check_ok == True)
        count_query = count_query.where(RadioStation.last_check_ok == True)

    statuses = [s.strip() for s in (params.status or "").split(",") if s.strip()]
    if statuses:
        health_includes = []
        for s in statuses:
            if s == "has_stream":
                query = query.where(RadioStation.last_check_ok == True)
                count_query = count_query.where(RadioStation.last_check_ok == True)
            elif s == "verified":
                health_includes.append(RadioStation.health_status == "verified")
            elif s == "live":
                health_includes.append(
                    RadioStation.health_status.in_(("verified", "online")) | (RadioStation.last_check_ok == True)
                )
            elif s == "hide_offline":
                cond = ~RadioStation.health_status.in_(("offline", "error", "timeout", "geo_blocked"))
                query = query.where(cond)
                count_query = count_query.where(cond)
        if health_includes:
            combined = health_includes[0] if len(health_includes) == 1 else or_(*health_includes)
            query = query.where(combined)
            count_query = count_query.where(combined)

    total = (await db.execute(count_query)).scalar() or 0

    offset = (params.page - 1) * params.per_page
    query = query.order_by(RadioStation.votes.desc()).offset(offset).limit(params.per_page)

    result = await db.execute(query)
    stations = result.scalars().all()
    return stations, total


async def get_radio_tags(db: AsyncSession, limit: int = 60):
    """Get top tags with station counts using SQL-side aggregation."""
    from sqlalchemy import text
    try:
        # Add explicit timeout for this expensive query
        await db.execute(text("SET LOCAL statement_timeout = '15000'"))  # 15 seconds
        
        result = await db.execute(text("""
            SELECT tag, COUNT(*) AS cnt
            FROM (
                SELECT lower(trim(unnest(string_to_array(tags, ',')))) AS tag
                FROM radio_stations
                WHERE tags != '' AND tags IS NOT NULL
                LIMIT 30000
            ) t
            WHERE length(tag) > 1
            GROUP BY tag
            ORDER BY cnt DESC
            LIMIT :lim
        """), {"lim": limit})
        return [{"name": row[0], "station_count": row[1]} for row in result]
    except Exception as e:
        logger.error(f"Error in get_radio_tags: {e}", exc_info=True)
        # Return empty list on error so it doesn't break the endpoint
        return []


async def get_radio_countries(db: AsyncSession):
    result = await db.execute(
        select(
            RadioStation.country,
            RadioStation.country_code,
            func.count(RadioStation.id).label("station_count"),
        )
        .where(RadioStation.country != "")
        .group_by(RadioStation.country, RadioStation.country_code)
        .having(func.count(RadioStation.id) > 0)
        .order_by(func.count(RadioStation.id).desc())
    )
    return result.all()


async def get_radio_stats(db: AsyncSession):
    total = (await db.execute(select(func.count(RadioStation.id)))).scalar() or 0
    working = (await db.execute(
        select(func.count(RadioStation.id)).where(RadioStation.last_check_ok == True)
    )).scalar() or 0
    return {"total": total, "working": working}
