"""AI-powered natural language search for channels and radio stations."""
import hashlib
import json
import logging
import re

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Channel, EpgProgramme, RadioStation
from app.redis_client import cache_get, cache_set
from app.services.epg_service import search_on_now

logger = logging.getLogger(__name__)

AI_CACHE_TTL = 600  # 10 minutes — AI results don't change often
MAX_CONTEXT_CHANNELS = 500  # Max channels to send as context to AI
FALLBACK_CANDIDATE_LIMIT = 200
FALLBACK_RESULT_LIMIT = 20

_FALLBACK_STOPWORDS = frozenset({
    "the", "a", "an", "for", "that", "show", "shows", "channels", "channel",
    "me", "find", "looking", "want", "with", "and", "or", "in", "of", "to",
    "from", "using", "keyword", "search", "right",
})

_INTENT_MAP: dict[str, list[str]] = {
    "soccer": ["sports", "football"],
    "football": ["sports", "football", "nfl"],
    "fifa": ["sports", "football", "soccer"],
    "worldcup": ["sports", "football", "soccer", "fifa"],
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

# Tokens that map to sports via INTENT_MAP, plus generic sports labels.
_SPORTS_INTENT_TOKENS = frozenset(
    {k for k, v in _INTENT_MAP.items() if "sports" in v} | {"sports", "sport"}
)
_LIVE_NOW_TOKENS = frozenset({"live", "now", "airing", "currently", "playing", "tonight"})


def _tokenize_fallback_query(query: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9+]+", query.lower())
    return [t for t in tokens if len(t) >= 2 and t not in _FALLBACK_STOPWORDS]


def _expand_search_terms(tokens: list[str]) -> list[str]:
    terms: set[str] = set(tokens)
    for token in tokens:
        expansions = _INTENT_MAP.get(token)
        if expansions:
            terms.update(expansions)
    return list(terms)


def _score_searchable(searchable: str, terms: list[str]) -> int:
    haystack = searchable.lower()
    return sum(1 for term in terms if term in haystack)


def _is_sports_on_now_intent(tokens: list[str]) -> bool:
    """True for sports queries (soccer/fifa/…) and live/now sports phrasing."""
    if not tokens:
        return False
    token_set = set(tokens)
    # live/now alone is not enough — need a sports token
    if token_set <= _LIVE_NOW_TOKENS:
        return False
    has_sports = bool(token_set & _SPORTS_INTENT_TOKENS)
    if not has_sports:
        expanded = set(_expand_search_terms(tokens))
        has_sports = bool(expanded & _SPORTS_INTENT_TOKENS) or "sports" in expanded
    return has_sports


def _sports_epg_query_params(tokens: list[str]) -> tuple[str | None, str | None]:
    """Pick ``q`` and/or ``category`` for ``search_on_now`` (prefer specific sport)."""
    specific = [t for t in tokens if t in _SPORTS_INTENT_TOKENS and t not in ("sports", "sport")]
    if specific:
        return specific[0], None
    if "sports" in tokens or "sport" in tokens:
        return None, "sports"
    for t in tokens:
        if t in _INTENT_MAP and "sports" in _INTENT_MAP[t]:
            return t, None
    return None, "sports"


def _channel_dict(channel: Channel, *, on_now_title: str | None = None) -> dict:
    out: dict = {
        "id": channel.id,
        "name": channel.name,
        "logo": channel.logo or "",
        "categories": channel.categories or "",
        "country_code": channel.country_code or "",
        "stream_url": channel.stream_url or "",
        "health_status": channel.health_status or "unknown",
    }
    if on_now_title is not None:
        out["on_now_title"] = on_now_title
    return out


async def _fetch_epg_sports_on_now(
    db: AsyncSession, tokens: list[str]
) -> list[EpgProgramme]:
    """Call EPG on-now helper; never raises — empty list on failure or no data."""
    q, category = _sports_epg_query_params(tokens)
    try:
        rows = await search_on_now(db, q=q, category=category, limit=50)
        if not rows and q and category is None:
            rows = await search_on_now(db, category="sports", limit=50)
        return rows
    except Exception as e:
        logger.warning("EPG on-now for AI search failed (non-fatal): %s", e)
        return []


async def _prepend_epg_on_now_channels(
    db: AsyncSession,
    query: str,
    channel_dicts: list[dict],
) -> tuple[list[dict], bool]:
    """Prefer channels with matching programmes airing now for sports queries."""
    tokens = _tokenize_fallback_query(query)
    if not tokens:
        stripped = query.lower().strip()
        tokens = [stripped] if stripped else []
    if not _is_sports_on_now_intent(tokens):
        return channel_dicts, False

    programmes = await _fetch_epg_sports_on_now(db, tokens)
    if not programmes:
        return channel_dicts, False

    title_by_id: dict[str, str] = {}
    ordered_ids: list[str] = []
    for prog in programmes:
        cid = prog.channel_id
        if cid not in title_by_id:
            title_by_id[cid] = prog.title or ""
            ordered_ids.append(cid)

    result = await db.execute(
        select(Channel)
        .where(Channel.id.in_(ordered_ids))
        .where(Channel.is_nsfw == False)
        .where(
            Channel.health_status.in_(
                ("verified", "online", "manifest_only", "unknown")
            )
        )
    )
    by_id = {c.id: c for c in result.scalars().all()}

    epg_dicts: list[dict] = []
    for cid in ordered_ids:
        channel = by_id.get(cid)
        if channel is not None:
            epg_dicts.append(_channel_dict(channel, on_now_title=title_by_id[cid]))

    if not epg_dicts:
        return channel_dicts, False

    seen = {d["id"] for d in epg_dicts}
    rest = [d for d in channel_dicts if d["id"] not in seen]
    merged = (epg_dicts + rest)[:FALLBACK_RESULT_LIMIT]
    return merged, True


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

        channel_dicts = [_channel_dict(c) for c in channels]
        channel_dicts, used_epg = await _prepend_epg_on_now_channels(
            db, query, channel_dicts
        )
        if used_epg and explanation:
            explanation = f"{explanation} Including programmes airing now."
        elif used_epg and not explanation:
            explanation = "Including channels with matching programmes airing now."

        response = {
            "channels": channel_dicts,
            "explanation": explanation,
            "query": query,
            "source": "ai+epg" if used_epg else "ai",
        }

        await cache_set(cache_key, response, AI_CACHE_TTL)
        logger.info(f"AI search for '{query}' returned {len(channel_dicts)} channels")
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
    db: AsyncSession, query: str, mode: str, _summaries: list[dict]
) -> dict:
    """Smart keyword fallback when AI is unavailable."""
    logger.info(f"Using fallback search for: {query}")
    tokens = _tokenize_fallback_query(query)
    if not tokens:
        stripped = query.lower().strip()
        tokens = [stripped] if stripped else []
    # DB filter uses query tokens only so broad intents (e.g. "sports") don't
    # flood the candidate cap and drop exact name hits like FIFA+.
    filter_terms = list(tokens)
    score_terms = _expand_search_terms(tokens)
    if not filter_terms:
        if mode == "tv":
            return {
                "channels": [],
                "explanation": f"Found 0 channels matching '{query}' using keyword search.",
                "query": query,
                "source": "fallback",
            }
        return {
            "stations": [],
            "explanation": f"Found 0 stations matching '{query}' using keyword search.",
            "query": query,
            "source": "fallback",
        }

    if mode == "tv":
        term_filters = [
            or_(
                Channel.name.ilike(f"%{term}%"),
                Channel.categories.ilike(f"%{term}%"),
                Channel.network.ilike(f"%{term}%"),
                Channel.country_code.ilike(f"%{term}%"),
                Channel.languages.ilike(f"%{term}%"),
            )
            for term in filter_terms
        ]
        result = await db.execute(
            select(Channel)
            .where(Channel.is_nsfw == False)
            .where(
                Channel.health_status.in_(
                    ("verified", "online", "manifest_only", "unknown")
                )
            )
            .where(or_(*term_filters))
            .order_by(Channel.name)
            .limit(FALLBACK_CANDIDATE_LIMIT)
        )
        candidates = result.scalars().all()
        scored: list[tuple[Channel, int]] = []
        for channel in candidates:
            name_l = (channel.name or "").lower()
            searchable = " ".join([
                channel.name or "",
                channel.categories or "",
                channel.network or "",
                channel.country_code or "",
                channel.languages or "",
            ])
            score = _score_searchable(searchable, score_terms)
            # Prefer channels whose name contains an original query token
            score += sum(3 for t in filter_terms if t in name_l)
            # Extra weight when an intent keyword (fifa, soccer, …) is in the name
            score += sum(2 for t in filter_terms if t in name_l and t in _INTENT_MAP)
            if score > 0:
                scored.append((channel, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        channels = [c for c, _ in scored[:FALLBACK_RESULT_LIMIT]]
        channel_dicts = [_channel_dict(c) for c in channels]
        channel_dicts, used_epg = await _prepend_epg_on_now_channels(
            db, query, channel_dicts
        )
        explanation = (
            f"Found {len(channel_dicts)} channels matching '{query}'"
            + (
                " (including programmes airing now)."
                if used_epg
                else " using keyword search."
            )
        )
        return {
            "channels": channel_dicts,
            "explanation": explanation,
            "query": query,
            "source": "fallback+epg" if used_epg else "fallback",
        }

    term_filters = [
        or_(
            RadioStation.name.ilike(f"%{term}%"),
            RadioStation.tags.ilike(f"%{term}%"),
            RadioStation.country_code.ilike(f"%{term}%"),
            RadioStation.language.ilike(f"%{term}%"),
        )
        for term in filter_terms
    ]
    result = await db.execute(
        select(RadioStation)
        .where(RadioStation.last_check_ok == True)
        .where(or_(*term_filters))
        .order_by(RadioStation.votes.desc())
        .limit(FALLBACK_CANDIDATE_LIMIT)
    )
    candidates = result.scalars().all()
    scored_stations: list[tuple[RadioStation, int]] = []
    for station in candidates:
        name_l = (station.name or "").lower()
        searchable = " ".join([
            station.name or "",
            station.tags or "",
            station.country_code or "",
            station.language or "",
        ])
        score = _score_searchable(searchable, score_terms)
        score += sum(3 for t in filter_terms if t in name_l)
        score += sum(2 for t in filter_terms if t in name_l and t in _INTENT_MAP)
        if score > 0:
            scored_stations.append((station, score))
    scored_stations.sort(key=lambda x: x[1], reverse=True)
    stations = [s for s, _ in scored_stations[:FALLBACK_RESULT_LIMIT]]
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
