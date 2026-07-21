import logging
import math
import random
from typing import Any

import httpx
from sqlalchemy import select, func, or_, and_, cast, Float
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models import RadioStation, UserVote
from app.schemas import (
    RadioSearchParams,
    MapStationPin,
    MapCluster,
    MapBboxResponse,
)

logger = logging.getLogger(__name__)

RADIO_API = "https://de1.api.radio-browser.info"

# Zoom below this returns grid clusters; at/above returns individual pins.
MAP_CLUSTER_ZOOM_MAX = 7
MAP_DEFAULT_LIMIT = 500
MAP_MAX_LIMIT = 2000
MAP_RIDE_NEAR_CANDIDATES = 40


def _geo_to_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _station_values_from_item(item: dict) -> dict | None:
    station_id = item.get("stationuuid", "")
    if not station_id:
        return None

    return {
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
        "geo_lat": _geo_to_str(item.get("geo_lat")),
        "geo_long": _geo_to_str(item.get("geo_long")),
    }


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

        values_batch = []
        for item in data:
            values = _station_values_from_item(item)
            if values is None:
                continue
            values_batch.append(values)

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


def parse_bbox(bbox: str) -> tuple[float, float, float, float]:
    """Parse `west,south,east,north` into floats. Raises ValueError on bad input.

    MapLibre world views can report longitudes outside [-180, 180]; clamp rather
    than 400 so low-zoom pan/zoom keeps working.
    """
    parts = [p.strip() for p in bbox.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be west,south,east,north")
    try:
        west, south, east, north = (float(p) for p in parts)
    except ValueError as exc:
        raise ValueError("bbox values must be numbers") from exc
    south = max(-90.0, min(90.0, south))
    north = max(-90.0, min(90.0, north))
    west = max(-180.0, min(180.0, west))
    east = max(-180.0, min(180.0, east))
    if south > north:
        raise ValueError("bbox south must be <= north")
    return west, south, east, north


def grid_cell_degrees(zoom: int) -> float:
    """Lat/lng grid cell size for clustering (degrees). Larger at low zoom."""
    z = max(0, int(zoom))
    return max(0.25, 40.0 / (2 ** z))


def should_return_clusters(zoom: int) -> bool:
    return int(zoom) <= MAP_CLUSTER_ZOOM_MAX


def cluster_points(
    points: list[tuple[float, float]],
    cell_degrees: float,
) -> list[MapCluster]:
    """Bucket (lat, lng) points into a simple grid; cluster center = mean of points."""
    if cell_degrees <= 0:
        raise ValueError("cell_degrees must be > 0")
    buckets: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for lat, lng in points:
        key = (math.floor(lat / cell_degrees), math.floor(lng / cell_degrees))
        buckets.setdefault(key, []).append((lat, lng))

    clusters: list[MapCluster] = []
    for pts in buckets.values():
        count = len(pts)
        avg_lat = sum(p[0] for p in pts) / count
        avg_lng = sum(p[1] for p in pts) / count
        clusters.append(MapCluster(lat=avg_lat, lng=avg_lng, count=count))
    return clusters


def _geo_lat_expr():
    return cast(RadioStation.geo_lat, Float)


def _geo_lng_expr():
    return cast(RadioStation.geo_long, Float)


def _has_geo_filter():
    return and_(
        RadioStation.geo_lat.isnot(None),
        RadioStation.geo_long.isnot(None),
        RadioStation.geo_lat != "",
        RadioStation.geo_long != "",
    )


def _bbox_filter(west: float, south: float, east: float, north: float):
    lat_f = _geo_lat_expr()
    lng_f = _geo_lng_expr()
    lat_cond = and_(lat_f >= south, lat_f <= north)
    if west <= east:
        lng_cond = and_(lng_f >= west, lng_f <= east)
    else:
        # Antimeridian wrap: e.g. west=170, east=-170
        lng_cond = or_(lng_f >= west, lng_f <= east)
    return and_(lat_cond, lng_cond)


async def get_map_bbox(
    db: AsyncSession,
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    zoom: int,
    limit: int = MAP_DEFAULT_LIMIT,
    working_only: bool = True,
) -> MapBboxResponse:
    """Stations or grid clusters inside bbox for MapLibre."""
    limit = max(1, min(int(limit), MAP_MAX_LIMIT))
    zoom = int(zoom)

    filters = [_has_geo_filter(), _bbox_filter(west, south, east, north)]
    if working_only:
        filters.append(RadioStation.last_check_ok == True)

    if should_return_clusters(zoom):
        cell = grid_cell_degrees(zoom)
        lat_f = _geo_lat_expr()
        lng_f = _geo_lng_expr()
        bucket_lat = func.floor(lat_f / cell)
        bucket_lng = func.floor(lng_f / cell)
        stmt = (
            select(
                func.avg(lat_f).label("lat"),
                func.avg(lng_f).label("lng"),
                func.count().label("count"),
            )
            .where(and_(*filters))
            .group_by(bucket_lat, bucket_lng)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        items = [
            MapCluster(lat=float(r.lat), lng=float(r.lng), count=int(r.count))
            for r in rows
            if r.lat is not None and r.lng is not None
        ]
        return MapBboxResponse(type="clusters", items=items, zoom=zoom)

    stmt = (
        select(RadioStation)
        .where(and_(*filters))
        .order_by(RadioStation.votes.desc())
        .limit(limit)
    )
    stations = (await db.execute(stmt)).scalars().all()
    items: list[MapStationPin] = []
    for s in stations:
        try:
            lat = float(s.geo_lat)
            lng = float(s.geo_long)
        except (TypeError, ValueError):
            continue
        items.append(
            MapStationPin(
                id=s.id,
                name=s.name or "",
                favicon=s.favicon or "",
                geo_lat=lat,
                geo_long=lng,
                country_code=s.country_code or "",
            )
        )
    return MapBboxResponse(type="stations", items=items, zoom=zoom)


async def get_ride_station(
    db: AsyncSession,
    *,
    lat: float | None = None,
    lng: float | None = None,
    working_only: bool = True,
) -> RadioStation | None:
    """Pick a random playable geo station; optionally biased near lat/lng."""
    filters = [_has_geo_filter()]
    if working_only:
        filters.append(RadioStation.last_check_ok == True)

    if lat is not None and lng is not None:
        lat_f = _geo_lat_expr()
        lng_f = _geo_lng_expr()
        dist_sq = (lat_f - lat) * (lat_f - lat) + (lng_f - lng) * (lng_f - lng)
        stmt = (
            select(RadioStation)
            .where(and_(*filters))
            .order_by(dist_sq.asc())
            .limit(MAP_RIDE_NEAR_CANDIDATES)
        )
        candidates = (await db.execute(stmt)).scalars().all()
        if not candidates:
            return None
        return random.choice(candidates)

    stmt = (
        select(RadioStation)
        .where(and_(*filters))
        .order_by(func.random())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()
