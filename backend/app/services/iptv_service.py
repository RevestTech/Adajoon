import logging
from datetime import datetime, timezone

import httpx

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.models import Channel, Category, Country, Language, Stream

logger = logging.getLogger(__name__)

API = settings.iptv_api_base


async def fetch_json(url: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def sync_categories(db: AsyncSession) -> int:
    data = await fetch_json(f"{API}/categories.json")
    for item in data:
        stmt = pg_insert(Category).values(
            id=item["id"], name=item["name"]
        ).on_conflict_do_update(index_elements=["id"], set_={"name": item["name"]})
        await db.execute(stmt)
    await db.commit()
    logger.info("Synced %d categories", len(data))
    return len(data)


async def sync_countries(db: AsyncSession) -> int:
    data = await fetch_json(f"{API}/countries.json")
    for item in data:
        stmt = pg_insert(Country).values(
            code=item["code"], name=item["name"], flag=item.get("flag", "")
        ).on_conflict_do_update(
            index_elements=["code"],
            set_={"name": item["name"], "flag": item.get("flag", "")},
        )
        await db.execute(stmt)
    await db.commit()
    logger.info("Synced %d countries", len(data))
    return len(data)


async def sync_languages(db: AsyncSession) -> int:
    data = await fetch_json(f"{API}/languages.json")
    for item in data:
        stmt = pg_insert(Language).values(
            code=item["code"], name=item["name"]
        ).on_conflict_do_update(index_elements=["code"], set_={"name": item["name"]})
        await db.execute(stmt)
    await db.commit()
    logger.info("Synced %d languages", len(data))
    return len(data)


async def sync_channels(db: AsyncSession) -> int:
    data = await fetch_json(f"{API}/channels.json")
    now = datetime.now(timezone.utc)
    insert_batch_size = 500
    
    # Prepare all values first
    values_batch = []
    for item in data:
        cats = item.get("categories", [])
        cat_id = cats[0] if cats else None
        langs = item.get("languages", [])

        values_batch.append({
            "id": item["id"],
            "name": item["name"],
            "alt_names": ";".join(item.get("alt_names", [])),
            "network": item.get("network", "") or "",
            "country_code": item.get("country", "") or "",
            "subdivision": item.get("subdivision", "") or "",
            "city": item.get("city", "") or "",
            "categories": ";".join(cats),
            "category_id": cat_id,
            "is_nsfw": item.get("is_nsfw", False),
            "launched": item.get("launched", "") or "",
            "closed": item.get("closed", "") or "",
            "website": item.get("website", "") or "",
            "logo": item.get("logo", "") or "",
            "languages": ";".join(langs),
            "is_active": not bool(item.get("closed")),
            "updated_at": now,
        })
    
    # Process in chunks
    count = 0
    for i in range(0, len(values_batch), insert_batch_size):
        chunk = values_batch[i:i + insert_batch_size]
        if not chunk:
            continue
            
        stmt = pg_insert(Channel).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": stmt.excluded.name,
                "alt_names": stmt.excluded.alt_names,
                "network": stmt.excluded.network,
                "country_code": stmt.excluded.country_code,
                "categories": stmt.excluded.categories,
                "category_id": stmt.excluded.category_id,
                "is_nsfw": stmt.excluded.is_nsfw,
                "logo": stmt.excluded.logo,
                "website": stmt.excluded.website,
                "languages": stmt.excluded.languages,
                "is_active": stmt.excluded.is_active,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        await db.execute(stmt)
        count += len(chunk)

    await db.commit()
    logger.info("Synced %d channels in batches of %d", count, insert_batch_size)
    return count


async def sync_streams(db: AsyncSession) -> int:
    data = await fetch_json(f"{API}/streams.json")
    count = 0

    known_ids_result = await db.execute(select(Channel.id))
    known_ids = {row[0] for row in known_ids_result}

    await db.execute(delete(Stream))

    for item in data:
        channel_id = item.get("channel")
        if not channel_id or channel_id not in known_ids:
            continue

        stream_stmt = pg_insert(Stream).values(
            channel_id=channel_id,
            url=item["url"],
            http_referrer=item.get("http_referrer", "") or "",
            user_agent=item.get("user_agent", "") or "",
            status=item.get("status", "unknown") or "unknown",
            added_at=datetime.now(timezone.utc),
        )
        await db.execute(stream_stmt)

        update_stmt = (
            Channel.__table__.update()
            .where(Channel.id == channel_id)
            .where(Channel.stream_url == "")
            .values(stream_url=item["url"])
        )
        await db.execute(update_stmt)
        count += 1

    await db.commit()
    logger.info("Synced %d streams", count)
    return count


async def full_sync(db: AsyncSession) -> dict:
    logger.info("Starting full IPTV data sync...")
    results = {}
    results["categories"] = await sync_categories(db)
    results["countries"] = await sync_countries(db)
    results["languages"] = await sync_languages(db)
    results["channels"] = await sync_channels(db)
    results["streams"] = await sync_streams(db)
    logger.info("Full sync complete: %s", results)
    return results
