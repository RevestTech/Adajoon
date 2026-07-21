"""Unit tests for EPG XMLTV parsing helpers."""
from datetime import timezone

import pytest

from app.services.epg_service import _normalize_channel_id, _parse_xmltv_time, parse_xmltv_programmes


@pytest.mark.unit
def test_normalize_channel_id_strips_at_suffix():
    assert _normalize_channel_id("CNN.us@East") == "CNN.us"
    assert _normalize_channel_id("BBCNews.uk") == "BBCNews.uk"


@pytest.mark.unit
def test_parse_xmltv_time_with_offset():
    dt = _parse_xmltv_time("20260402120000 +0000")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.astimezone(timezone.utc).hour == 12


@pytest.mark.unit
def test_parse_xmltv_programmes():
    xml = b"""<?xml version="1.0"?>
    <tv>
      <programme start="20260402120000 +0000" stop="20260402130000 +0000" channel="Test.uk">
        <title>Match Day</title>
        <sub-title>Live</sub-title>
        <desc>Football</desc>
        <category>Sports</category>
      </programme>
    </tv>
    """
    rows = parse_xmltv_programmes(xml)
    assert len(rows) == 1
    assert rows[0]["channel_id"] == "Test.uk"
    assert rows[0]["title"] == "Match Day"
    assert "Sports" in rows[0]["category"]
