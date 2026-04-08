"""AI-powered natural language search for channels and radio stations."""
import hashlib
import json
import logging
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Channel, RadioStation
from app.redis_client import cache_get, cache_set

logger = logging.getLogger(__name__)

AI_CACHE_TTL = 600  # 10 minutes — AI results don't change often
MAX_CONTEXT_CHANNELS = 500  # Max channels to send as context to AI


def _cache_key(query: str, mode: str) -> str:
    """Generate a cache key for an AI search query."""
    h = hashlib.md5(f"{mode}:{query.lower().strip()}".encode()).hexdigest()
    return f"ai_search:{h}"


async def _get_channel_summaries(db: AsyncSession) -> list[dict]:
    """Get a compact summary of all channels for AI context."""
    cached = await cache_get("ai_channel_summaries")
    if cached:
        return cached

    result = await db.execute(
        select(
            Channel.id,
            Channel.name,
            Channel.categories,
            Channel.country_code,
            Channel.languages,
            Channel.network,
        )
        .where(Channel.is_nsfw == False)
        .where(Channel.health_status.in_(("verified", "online", "manifest_only", "unknown")))
        .order_by(Channel.name)
        .limit(MAX_CONTEXT_CHANNELS)
    )
    rows = result.all()
    summaries = [
        {
            "id": r.id,
            "name": r.name,
            "categories": r.categories or "",
            "country": r.country_code or "",
            "languages": r.languages or "",
            "network": r.network or "",
        }
        for r in rows
    ]
    await cache_set("ai_channel_summaries", summaries, 300)
    return summaries


async def _get_radio_summaries(db: AsyncSession) -> list[dict]:
    """Get a compact summary of all radio stations for AI context."""
    cached = await cache_get("ai_radio_summaries")
    if cached:
        return cached

    result = await db.execute(
        select(
            RadioStation.id,
            RadioStation.name,
            RadioStation.tags,
            RadioStation.country_code,
            RadioStation.language,
        )
        .where(RadioStation.last_check_ok == True)
        .order_by(RadioStation.votes.desc())
        .limit(MAX_CONTEXT_CHANNELS)
    )
    rows = result.all()
    summaries = [
        {
            "id": str(r.id),
            "name": r.name,
            "tags": r.tags or "",
            "country": r.country_code or "",
            "language": r.language or "",
        }
        for r in rows
    ]
    await cache_set("ai_radio_summaries", summaries, 300)
    return summaries


async def ai_search_channels(
    db: AsyncSession, query: str
) -> dict:
    """Use Claude to find channels matching a natural language query."""
    cache_key = _cache_key(query, "tv")
    cached = await cache_get(cache_key)
    if cached:
        logger.info(f"AI search cache hit for: {query}")
        return cached

    summaries = await _get_channel_summaries(db)

    if not settings.anthropic_api_key:
        # Fallback: smart keyword matching
        return await _fallback_search(db, query, "tv", summaries)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        channel_context = json.dumps(summaries, separators=(",", ":"))

        message = client.messages.create(
            model=settings.ai_model,
            max_tokens=1024,
            system=(
                "You are a TV channel search assistant for the Adajoon streaming platform. "
                "Given a user's natural language query, find the most relevant channels from the provided list. "
                "Return ONLY a JSON object with: "
                '{"channel_ids": ["id1", "id2", ...], "explanation": "brief explanation of why these match"} '
                "Return up to 20 matching channels, ordered by relevance. "
                "Consider channel names, categories, countries, languages, and networks. "
                "For sports queries, look for 'sports' category and sport-related names. "
                "For news, look for 'news' category. For music, look for 'music' category. "
                "For country-specific requests, match the country code. "
                "If no channels match well, return an empty array with an explanation."
            ),
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Find channels matching: \"{query}\"\n\n"
                        f"Available channels:\n{channel_context}"
                    ),
                }
            ],
        )

        response_text = message.content[0].text
        # Parse JSON from response (handle markdown code blocks)
        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        parsed = json.loads(response_text)
        channel_ids = parsed.get("channel_ids", [])
        explanation = parsed.get("explanation", "")

        # Fetch full channel objects for matched IDs
        if channel_ids:
            result = await db.execute(
                select(Channel).where(Channel.id.in_(channel_ids))
            )
            channels = result.scalars().all()
            # Preserve AI-determined order
            id_order = {cid: idx for idx, cid in enumerate(channel_ids)}
            channels = sorted(channels, key=lambda c: id_order.get(c.id, 999))
        else:
            channels = []

        response = {
            "channels": [
                {
                    "id": c.id,
                    "name": c.name,
                    "logo": c.logo or "",
                    "categories": c.categories or "",
                    "country_code": c.country_code or "",
                    "stream_url": c.stream_url or "",
                    "health_status": c.health_status or "unknown",
                }
                for c in channels
            ],
            "explanation": explanation,
            "query": query,
            "source": "ai",
        }

        await cache_set(cache_key, response, AI_CACHE_TTL)
        logger.info(f"AI search for '{query}' returned {len(channels)} channels")
        return response

    except Exception as e:
        logger.error(f"AI search failed: {e}", exc_info=True)
        return await _fallback_search(db, query, "tv", summaries)


async def ai_search_radio(
    db: AsyncSession, query: str
) -> dict:
    """Use Claude to find radio stations matching a natural language query."""
    cache_key = _cache_key(query, "radio")
    cached = await cache_get(cache_key)
    if cached:
        logger.info(f"AI radio search cache hit for: {query}")
        return cached

    summaries = await _get_radio_summaries(db)

    if not settings.anthropic_api_key:
        return await _fallback_search(db, query, "radio", summaries)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        station_context = json.dumps(summaries, separators=(",", ":"))

        message = client.messages.create(
            model=settings.ai_model,
            max_tokens=1024,
            system=(
                "You are a radio station search assistant for the Adajoon streaming platform. "
                "Given a user's natural language query, find the most relevant radio stations from the provided list. "
                "Return ONLY a JSON object with: "
                '{"station_ids": ["id1", "id2", ...], "explanation": "brief explanation of why these match"} '
                "Return up to 20 matching stations, ordered by relevance. "
                "Consider station names, tags/genres, countries, and languages. "
                "If no stations match well, return an empty array with an explanation."
            ),
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Find radio stations matching: \"{query}\"\n\n"
                        f"Available stations:\n{station_context}"
                    ),
                }
            ],
        )

        response_text = message.content[0].text
        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        parsed = json.loads(response_text)
        station_ids = parsed.get("station_ids", [])
        explanation = parsed.get("explanation", "")

        # Convert to integers for DB lookup
        int_ids = []
        for sid in station_ids:
            try:
                int_ids.append(int(sid))
            except (ValueError, TypeError):
                continue

        if int_ids:
            result = await db.execute(
                select(RadioStation).where(RadioStation.id.in_(int_ids))
            )
            stations = result.scalars().all()
            id_order = {sid: idx for idx, sid in enumerate(int_ids)}
            stations = sorted(stations, key=lambda s: id_order.get(s.id, 999))
        else:
            stations = []

        response = {
            "stations": [
                {
                    "id": s.id,
                    "name": s.name,
                    "favicon": s.favicon or "",
                    "tags": s.tags or "",
                    "country_code": s.country_code or "",
                    "url": s.url or "",
                    "url_resolved": s.url_resolved or "",
                }
                for s in stations
            ],
            "explanation": explanation,
            "query": query,
            "source": "ai",
        }

        await cache_set(cache_key, response, AI_CACHE_TTL)
        logger.info(f"AI radio search for '{query}' returned {len(stations)} stations")
        return response

    except Exception as e:
        logger.error(f"AI radio search failed: {e}", exc_info=True)
        return await _fallback_search(db, query, "radio", summaries)


async def _fallback_search(
    db: AsyncSession, query: str, mode: str, summaries: list[dict]
) -> dict:
    """Smart keyword fallback when AI is unavailable."""
    logger.info(f"Using fallback search for: {query}")
    query_lower = query.lower()

    # Common intent keywords mapped to categories/tags
    INTENT_MAP = {
        "soccer": ["sports", "football"],
        "football": ["sports", "football", "nfl"],
        "basketball": ["sports", "basketball", "nba"],
        "baseball": ["sports", "baseball", "mlb"],
        "tennis": ["sports", "tennis"],
        "cricket": ["sports", "cricket"],
        "golf": ["sports", "golf"],
        "news": ["news"],
        "music": ["music"],
        "kids": ["kids", "children", "animation"],
        "movies": ["movies", "cinema", "film"],
        "documentary": ["documentary"],
        "cooking": ["cooking", "food"],
        "comedy": ["comedy"],
        "science": ["science", "education"],
        "religious": ["religious", "religion"],
        "weather": ["weather"],
        "entertainment": ["entertainment"],
        "persian": ["persian", "iran", "IR"],
        "arabic": ["arabic", "arab"],
        "spanish": ["spanish"],
        "french": ["french"],
        "chinese": ["chinese", "CN"],
        "japanese": ["japanese", "JP"],
        "korean": ["korean", "KR"],
        "turkish": ["turkish", "TR"],
        "indian": ["indian", "hindi", "IN"],
        "german": ["german", "DE"],
        "italian": ["italian", "IT"],
        "russian": ["russian", "RU"],
        "brazilian": ["brazilian", "portuguese", "BR"],
    }

    # Expand query into search terms
    search_terms = [query_lower]
    for keyword, expansions in INTENT_MAP.items():
        if keyword in query_lower:
            search_terms.extend(expansions)

    search_terms = list(set(search_terms))

    # Score each summary by how many terms match
    scored = []
    for item in summaries:
        searchable = " ".join([
            item.get("name", ""),
            item.get("categories", item.get("tags", "")),
            item.get("country", ""),
            item.get("languages", item.get("language", "")),
            item.get("network", ""),
        ]).lower()

        score = sum(1 for term in search_terms if term in searchable)
        if score > 0:
            scored.append((item["id"], score))

    # Sort by score descending, take top 20
    scored.sort(key=lambda x: x[1], reverse=True)
    top_ids = [item_id for item_id, _ in scored[:20]]

    if mode == "tv":
        if top_ids:
            result = await db.execute(
                select(Channel).where(Channel.id.in_(top_ids))
            )
            channels = result.scalars().all()
            id_order = {cid: idx for idx, cid in enumerate(top_ids)}
            channels = sorted(channels, key=lambda c: id_order.get(c.id, 999))
        else:
            channels = []

        return {
            "channels": [
                {
                    "id": c.id,
                    "name": c.name,
                    "logo": c.logo or "",
                    "categories": c.categories or "",
                    "country_code": c.country_code or "",
                    "stream_url": c.stream_url or "",
                    "health_status": c.health_status or "unknown",
                }
                for c in channels
            ],
            "explanation": f"Found {len(channels)} channels matching '{query}' using keyword search.",
            "query": query,
            "source": "fallback",
        }
    else:
        int_ids = []
        for sid in top_ids:
            try:
                int_ids.append(int(sid))
            except (ValueError, TypeError):
                continue

        if int_ids:
            result = await db.execute(
                select(RadioStation).where(RadioStation.id.in_(int_ids))
            )
            stations = result.scalars().all()
            id_order = {sid: idx for idx, sid in enumerate(int_ids)}
            stations = sorted(stations, key=lambda s: id_order.get(s.id, 999))
        else:
            stations = []

        return {
            "stations": [
                {
                    "id": s.id,
                    "name": s.name,
                    "favicon": s.favicon or "",
                    "tags": s.tags or "",
                    "country_code": s.country_code or "",
                    "url": s.url or "",
                    "url_resolved": s.url_resolved or "",
                }
                for s in stations
            ],
            "explanation": f"Found {len(stations)} stations matching '{query}' using keyword search.",
            "query": query,
            "source": "fallback",
        }
