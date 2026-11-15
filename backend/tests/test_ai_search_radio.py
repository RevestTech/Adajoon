"""Regression test for the AI radio search UUID bug: ai_search_radio used
to run int(station_id) on Radio-Browser's UUID station ids, which always
raised and silently dropped every match, so the endpoint always returned
zero stations regardless of what the AI actually matched."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RadioStation
from app.services.ai_search_service import ai_search_radio


def _fake_anthropic_message(json_text: str):
    block = MagicMock()
    block.text = json_text
    message = MagicMock()
    message.content = [block]
    return message


@pytest.mark.unit
async def test_ai_search_radio_returns_matched_stations_by_uuid(
    test_db: AsyncSession, monkeypatch
):
    monkeypatch.setattr(
        "app.services.ai_search_service.settings.anthropic_api_key", "fake-key"
    )

    station = RadioStation(
        id="9617a958-0601-11e8-ae97-52543be04c81",
        name="Classic Rock FM",
        tags="rock,classic",
        language="english",
        codec="MP3",
        bitrate=128,
        votes=42,
        homepage="https://example.com",
        country="United States",
        country_code="US",
    )
    test_db.add(station)
    await test_db.commit()

    fake_client = MagicMock()
    fake_client.messages.create = AsyncMock(
        return_value=_fake_anthropic_message(
            '{"station_ids": ["9617a958-0601-11e8-ae97-52543be04c81"], '
            '"explanation": "classic rock match"}'
        )
    )

    with patch("anthropic.AsyncAnthropic", return_value=fake_client):
        response = await ai_search_radio(test_db, "classic rock")

    assert response["source"] == "ai"
    assert len(response["stations"]) == 1
    result = response["stations"][0]
    assert result["id"] == "9617a958-0601-11e8-ae97-52543be04c81"
    assert result["name"] == "Classic Rock FM"
    # Full RadioStationOut shape, not the old hand-rolled subset - fixes the
    # separately-flagged "incomplete metadata" finding alongside the bug.
    assert result["language"] == "english"
    assert result["codec"] == "MP3"
    assert result["bitrate"] == 128
    assert result["votes"] == 42
    assert result["homepage"] == "https://example.com"
    assert result["country"] == "United States"
