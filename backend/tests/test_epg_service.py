"""Unit tests for XMLTV EPG parse, prune helpers, and country failure isolation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.epg_service import (
    guide_urls_for_country,
    parse_xmltv_datetime,
    parse_xmltv_programmes,
    prune_old_programmes,
    sync_epg,
)

SAMPLE_XMLTV = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE tv SYSTEM "xmltv.dtd">
<tv>
  <channel id="BBCOne.uk">
    <display-name>BBC One</display-name>
  </channel>
  <programme start="20240101120000 +0000" stop="20240101130000 +0000" channel="BBCOne.uk">
    <title lang="en">News at Noon</title>
    <sub-title lang="en">World edition</sub-title>
    <desc lang="en">Daily news bulletin.</desc>
    <category lang="en">News</category>
  </programme>
  <programme start="20240101130000 +0000" stop="20240101140000 +0000" channel="CNN.us">
    <title>Sports Desk</title>
    <category>Sports</category>
    <category>News</category>
  </programme>
  <programme start="bad" stop="20240101140000 +0000" channel="Broken.uk">
    <title>Skip me</title>
  </programme>
</tv>
"""


@pytest.mark.unit
def test_parse_xmltv_datetime_with_offset() -> None:
    dt = parse_xmltv_datetime("20240101123000 +0000")
    assert dt is not None
    assert dt == datetime(2024, 1, 1, 12, 30, tzinfo=timezone.utc)


@pytest.mark.unit
def test_parse_xmltv_datetime_negative_offset() -> None:
    dt = parse_xmltv_datetime("20240101120000 -0500")
    assert dt is not None
    assert dt.utcoffset() == timedelta(hours=-5)


@pytest.mark.unit
def test_parse_xmltv_programmes_fixture() -> None:
    programmes = parse_xmltv_programmes(SAMPLE_XMLTV)
    assert len(programmes) == 2

    first = programmes[0]
    assert first["channel_id"] == "BBCOne.uk"
    assert first["title"] == "News at Noon"
    assert first["subtitle"] == "World edition"
    assert first["description"] == "Daily news bulletin."
    assert first["category"] == "News"
    assert first["start_at"] == datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert first["stop_at"] == datetime(2024, 1, 1, 13, 0, tzinfo=timezone.utc)

    second = programmes[1]
    assert second["channel_id"] == "CNN.us"
    assert second["category"] == "Sports,News"


@pytest.mark.unit
def test_guide_urls_for_country_include_gz() -> None:
    urls = guide_urls_for_country("us")
    assert any(u.endswith("/us/tvtv.us.epg.xml") for u in urls)
    assert any(u.endswith("/us/tvtv.us.epg.xml.gz") for u in urls)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prune_old_programmes_deletes_before_cutoff() -> None:
    db = AsyncMock()
    result = MagicMock()
    result.rowcount = 3
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()

    deleted = await prune_old_programmes(db, older_than_days=2)

    assert deleted == 3
    db.execute.assert_awaited_once()
    db.commit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_epg_isolates_country_http_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EPG_COUNTRY_CODES", "us,uk")

    call_count = {"n": 0}

    async def fake_sync_country_pack(db, country_code, client=None):
        call_count["n"] += 1
        if country_code == "us":
            return {
                "upserted": 0,
                "error": "Client error '404 Not Found' for url 'https://example/us.xml'",
                "url": None,
            }
        return {
            "upserted": 12,
            "error": None,
            "url": "https://iptv-org.github.io/epg/guides/uk/sky.com.epg.xml",
        }

    db = AsyncMock()

    with (
        patch(
            "app.services.epg_service.sync_country_pack",
            side_effect=fake_sync_country_pack,
        ),
        patch(
            "app.services.epg_service.prune_old_programmes",
            new=AsyncMock(return_value=1),
        ),
        patch("app.services.epg_service.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        summary = await sync_epg(db)

    assert call_count["n"] == 2
    assert summary["countries"]["us"]["error"]
    assert summary["countries"]["uk"]["upserted"] == 12
    assert summary["countries"]["uk"]["error"] is None
    assert summary["pruned"] == 1
    assert any(e["country"] == "us" for e in summary["errors"])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_country_pack_continues_after_http_error() -> None:
    from app.services.epg_service import sync_country_pack

    client = AsyncMock(spec=httpx.AsyncClient)
    # First URL fails, second (.gz) succeeds with fixture
    fail_resp = MagicMock()
    fail_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404",
        request=MagicMock(),
        response=MagicMock(status_code=404),
    )
    ok_resp = MagicMock()
    ok_resp.raise_for_status = MagicMock()
    ok_resp.content = SAMPLE_XMLTV

    client.get = AsyncMock(side_effect=[fail_resp, ok_resp])

    db = AsyncMock()

    with patch(
        "app.services.epg_service.upsert_programmes",
        new=AsyncMock(return_value=2),
    ) as upsert:
        result = await sync_country_pack(db, "us", client=client)

    assert result["error"] is None
    assert result["upserted"] == 2
    upsert.assert_awaited_once()
    assert client.get.await_count == 2
