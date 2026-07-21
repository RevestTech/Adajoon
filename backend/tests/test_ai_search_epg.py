"""Unit tests for AI/keyword search + EPG on-now sports wiring."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_search_service import (
    _is_sports_on_now_intent,
    _prepend_epg_on_now_channels,
    _sports_epg_query_params,
    _tokenize_fallback_query,
    ai_search_channels,
)


@pytest.mark.unit
def test_sports_on_now_intent_detects_sport_tokens() -> None:
    assert _is_sports_on_now_intent(["soccer"])
    assert _is_sports_on_now_intent(["football"])
    assert _is_sports_on_now_intent(["fifa"])
    assert _is_sports_on_now_intent(["live", "sports"])
    assert _is_sports_on_now_intent(_tokenize_fallback_query("soccer right now"))
    assert _is_sports_on_now_intent(_tokenize_fallback_query("live sports"))


@pytest.mark.unit
def test_sports_on_now_intent_rejects_non_sports() -> None:
    assert not _is_sports_on_now_intent(["news"])
    assert not _is_sports_on_now_intent(["cooking"])
    assert not _is_sports_on_now_intent(["live", "now"])  # live/now alone
    assert not _is_sports_on_now_intent([])


@pytest.mark.unit
def test_sports_epg_query_params_prefer_specific_sport() -> None:
    assert _sports_epg_query_params(["soccer", "now"]) == ("soccer", None)
    assert _sports_epg_query_params(["live", "sports"]) == (None, "sports")
    assert _sports_epg_query_params(["fifa"]) == ("fifa", None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prepend_epg_prefers_on_now_channels() -> None:
    prog = MagicMock()
    prog.channel_id = "ESPN.us"
    prog.title = "Premier League Live"

    espn = MagicMock()
    espn.id = "ESPN.us"
    espn.name = "ESPN"
    espn.logo = ""
    espn.categories = "sports"
    espn.country_code = "US"
    espn.stream_url = "https://example/espn"
    espn.health_status = "online"

    name_only = {
        "id": "SportsNet.us",
        "name": "SportsNet",
        "logo": "",
        "categories": "sports",
        "country_code": "US",
        "stream_url": "https://example/sn",
        "health_status": "online",
    }

    channel_result = MagicMock()
    channel_result.scalars.return_value.all.return_value = [espn]
    db = AsyncMock()
    db.execute = AsyncMock(return_value=channel_result)

    with patch(
        "app.services.ai_search_service.search_on_now",
        new=AsyncMock(return_value=[prog]),
    ) as mock_epg:
        merged, used = await _prepend_epg_on_now_channels(
            db, "soccer right now", [name_only]
        )

    assert used is True
    assert merged[0]["id"] == "ESPN.us"
    assert merged[0]["on_now_title"] == "Premier League Live"
    assert merged[1]["id"] == "SportsNet.us"
    mock_epg.assert_awaited()
    call_kwargs = mock_epg.await_args.kwargs
    assert call_kwargs.get("q") == "soccer"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prepend_epg_empty_falls_back() -> None:
    name_only = {
        "id": "SportsNet.us",
        "name": "SportsNet",
        "logo": "",
        "categories": "sports",
        "country_code": "US",
        "stream_url": "https://example/sn",
        "health_status": "online",
    }
    db = AsyncMock()

    with patch(
        "app.services.ai_search_service.search_on_now",
        new=AsyncMock(return_value=[]),
    ):
        merged, used = await _prepend_epg_on_now_channels(
            db, "soccer", [name_only]
        )

    assert used is False
    assert merged == [name_only]
    db.execute.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prepend_epg_skips_non_sports_query() -> None:
    db = AsyncMock()
    channels = [{"id": "CNN.us", "name": "CNN"}]

    with patch(
        "app.services.ai_search_service.search_on_now",
        new=AsyncMock(),
    ) as mock_epg:
        merged, used = await _prepend_epg_on_now_channels(db, "world news", channels)

    assert used is False
    assert merged == channels
    mock_epg.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prepend_epg_failure_is_non_fatal() -> None:
    channels = [{"id": "SportsNet.us", "name": "SportsNet"}]
    db = AsyncMock()

    with patch(
        "app.services.ai_search_service.search_on_now",
        new=AsyncMock(side_effect=RuntimeError("db down")),
    ):
        merged, used = await _prepend_epg_on_now_channels(db, "fifa", channels)

    assert used is False
    assert merged == channels


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ai_search_channels_fallback_merges_epg(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ai_search_service.settings.anthropic_api_key", ""
    )
    monkeypatch.setattr(
        "app.services.ai_search_service.cache_get",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.services.ai_search_service.cache_set",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.services.ai_search_service._get_channel_summaries",
        AsyncMock(return_value=[]),
    )

    sports_chan = MagicMock()
    sports_chan.id = "BeINSports.us"
    sports_chan.name = "beIN Sports"
    sports_chan.logo = ""
    sports_chan.categories = "sports"
    sports_chan.country_code = "US"
    sports_chan.network = ""
    sports_chan.languages = "English"
    sports_chan.stream_url = "https://example/bein"
    sports_chan.health_status = "online"

    keyword_result = MagicMock()
    keyword_result.scalars.return_value.all.return_value = [sports_chan]

    epg_chan = MagicMock()
    epg_chan.id = "ESPN.us"
    epg_chan.name = "ESPN"
    epg_chan.logo = ""
    epg_chan.categories = "sports"
    epg_chan.country_code = "US"
    epg_chan.stream_url = "https://example/espn"
    epg_chan.health_status = "online"

    epg_channel_result = MagicMock()
    epg_channel_result.scalars.return_value.all.return_value = [epg_chan]

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[keyword_result, epg_channel_result])

    prog = MagicMock()
    prog.channel_id = "ESPN.us"
    prog.title = "MLS Soccer"

    with patch(
        "app.services.ai_search_service.search_on_now",
        new=AsyncMock(return_value=[prog]),
    ):
        resp = await ai_search_channels(db, "soccer right now")

    assert resp["source"] == "fallback+epg"
    assert resp["channels"][0]["id"] == "ESPN.us"
    assert resp["channels"][0]["on_now_title"] == "MLS Soccer"
    ids = [c["id"] for c in resp["channels"]]
    assert "BeINSports.us" in ids
