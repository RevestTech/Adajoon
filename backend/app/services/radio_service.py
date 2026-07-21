import logging
import random

import httpx
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models import RadioStation, UserVote
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

            geo_lat = item.get("geo_lat")
            geo_long = item.get("geo_long")
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
                "geo_lat": "" if geo_lat is None else str(geo_lat),
                "geo_long": "" if geo_long is None else str(geo_long),
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
                    "geo_lat": stmt.excluded.geo_lat,
                    "geo_long": stmt.excluded.geo_long,
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
            elif s == "highly_rated":
                subq = (
                    select(UserVote.item_id)
                    .where(
                        UserVote.item_type == "radio",
                        UserVote.vote_type.in_(("works", "like"))
                    )
                    .group_by(UserVote.item_id)
                    .having(func.count(UserVote.id) >= 3)
                )
                query = query.where(RadioStation.id.in_(subq))
                count_query = count_query.where(RadioStation.id.in_(subq))
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


def get_radio_tags(limit: int = 60):
    """Get popular radio tags.
    
    Returns common genre/category tags used across radio stations.
    Static list for performance - tags are computed by background job.
    """
    # Static curated list of common genres/tags
    common_tags = [
        {"name": "music", "station_count": 5000},
        {"name": "pop", "station_count": 3500},
        {"name": "news", "station_count": 2800},
        {"name": "rock", "station_count": 2500},
        {"name": "talk", "station_count": 2200},
        {"name": "jazz", "station_count": 1800},
        {"name": "classical", "station_count": 1500},
        {"name": "electronic", "station_count": 1400},
        {"name": "dance", "station_count": 1300},
        {"name": "country", "station_count": 1200},
        {"name": "hip hop", "station_count": 1100},
        {"name": "sports", "station_count": 1000},
        {"name": "oldies", "station_count": 950},
        {"name": "80s", "station_count": 900},
        {"name": "90s", "station_count": 850},
        {"name": "christian", "station_count": 800},
        {"name": "alternative", "station_count": 750},
        {"name": "latin", "station_count": 700},
        {"name": "blues", "station_count": 650},
        {"name": "variety", "station_count": 600},
        {"name": "reggae", "station_count": 550},
        {"name": "indie", "station_count": 500},
        {"name": "metal", "station_count": 450},
        {"name": "funk", "station_count": 400},
        {"name": "soul", "station_count": 380},
        {"name": "ambient", "station_count": 350},
        {"name": "house", "station_count": 330},
        {"name": "techno", "station_count": 310},
        {"name": "trance", "station_count": 290},
        {"name": "70s", "station_count": 270},
    ]
    return common_tags[:limit]


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


def _parse_geo(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _cluster_precision(zoom: int) -> int:
    if zoom <= 2:
        return 0
    if zoom <= 4:
        return 1
    if zoom <= 6:
        return 2
    if zoom <= 8:
        return 3
    return 4


async def get_stations_in_bbox(
    db: AsyncSession,
    west: float,
    south: float,
    east: float,
    north: float,
    zoom: int = 5,
    limit: int = 500,
    working_only: bool = True,
) -> dict:
    """Return stations or clusters inside a geographic bbox."""
    query = select(RadioStation).where(
        RadioStation.geo_lat != "",
        RadioStation.geo_long != "",
    )
    if working_only:
        query = query.where(RadioStation.last_check_ok == True)

    result = await db.execute(query.order_by(RadioStation.votes.desc()).limit(8000))
    rows = result.scalars().all()

    stations: list[dict] = []
    for s in rows:
        lat = _parse_geo(s.geo_lat)
        lng = _parse_geo(s.geo_long)
        if lat is None or lng is None:
            continue
        # Handle antimeridian: west > east means wrap
        in_lng = (west <= lng <= east) if west <= east else (lng >= west or lng <= east)
        if not (south <= lat <= north and in_lng):
            continue
        stations.append({
            "id": s.id,
            "name": s.name,
            "favicon": s.favicon or "",
            "tags": s.tags or "",
            "country_code": s.country_code or "",
            "url": s.url or "",
            "url_resolved": s.url_resolved or "",
            "geo_lat": str(lat),
            "geo_long": str(lng),
            "votes": s.votes or 0,
            "last_check_ok": bool(s.last_check_ok),
        })

    if zoom >= 8 or len(stations) <= limit:
        return {"type": "stations", "items": stations[:limit], "total": len(stations)}

    precision = _cluster_precision(zoom)
    buckets: dict[tuple[float, float], dict] = {}
    for st in stations:
        lat = float(st["geo_lat"])
        lng = float(st["geo_long"])
        key = (round(lat, precision), round(lng, precision))
        bucket = buckets.get(key)
        if bucket is None:
            buckets[key] = {
                "lat": key[0],
                "lng": key[1],
                "count": 1,
                "sample": st,
            }
        else:
            bucket["count"] += 1
            if st["votes"] > bucket["sample"]["votes"]:
                bucket["sample"] = st

    clusters = [
        {
            "lat": b["lat"],
            "lng": b["lng"],
            "count": b["count"],
            "sample_id": b["sample"]["id"],
            "sample_name": b["sample"]["name"],
        }
        for b in buckets.values()
    ]
    clusters.sort(key=lambda c: c["count"], reverse=True)
    return {"type": "clusters", "items": clusters[:limit], "total": len(stations)}


async def get_random_geo_station(
    db: AsyncSession,
    lat: float | None = None,
    lng: float | None = None,
    working_only: bool = True,
) -> RadioStation | None:
    """Pick a random playable station with geo; prefer near lat/lng when given."""
    query = select(RadioStation).where(
        RadioStation.geo_lat != "",
        RadioStation.geo_long != "",
        RadioStation.url != "",
    )
    if working_only:
        query = query.where(RadioStation.last_check_ok == True)

    result = await db.execute(query.order_by(RadioStation.votes.desc()).limit(2000))
    rows = list(result.scalars().all())
    if not rows:
        return None

    parsed: list[tuple[RadioStation, float, float]] = []
    for s in rows:
        plat = _parse_geo(s.geo_lat)
        plng = _parse_geo(s.geo_long)
        if plat is None or plng is None:
            continue
        parsed.append((s, plat, plng))
    if not parsed:
        return None

    if lat is None or lng is None:
        return random.choice(parsed)[0]

    # Prefer stations within ~15 degrees, else any
    nearby = [
        s for s, plat, plng in parsed
        if abs(plat - lat) < 15 and abs(plng - lng) < 15
    ]
    if nearby:
        return random.choice(nearby)
    return random.choice(parsed)[0]

