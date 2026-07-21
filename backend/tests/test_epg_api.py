"""Unit tests for EPG API schemas and query helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.schemas import (
    EpgNowResponse,
    EpgOnNowItem,
    EpgOnNowResponse,
    EpgProgrammeOut,
    EpgScheduleResponse,
)
from app.services.epg_service import (
    is_airing_at,
    matches_on_now_text,
    overlaps_window,
    resolve_schedule_window,
    get_now_next,
    search_on_now,
)


FIXED_NOW = datetime(2026, 7, 20, 15, 0, tzinfo=timezone.utc)


@pytest.mark.unit
def test_resolve_schedule_window_defaults() -> None:
    start, end = resolve_schedule_window(None, None, now=FIXED_NOW)
    assert start == FIXED_NOW
    assert end == FIXED_NOW + timedelta(hours=24)


@pytest.mark.unit
def test_resolve_schedule_window_partial_from() -> None:
    from_dt = FIXED_NOW - timedelta(hours=1)
    start, end = resolve_schedule_window(from_dt, None, now=FIXED_NOW)
    assert start == from_dt
    assert end == FIXED_NOW + timedelta(hours=24)


@pytest.mark.unit
def test_resolve_schedule_window_rejects_inverted() -> None:
    with pytest.raises(ValueError, match="to must be after from"):
        resolve_schedule_window(FIXED_NOW, FIXED_NOW - timedelta(minutes=1), now=FIXED_NOW)


@pytest.mark.unit
def test_overlaps_window() -> None:
    a = FIXED_NOW
    b = FIXED_NOW + timedelta(hours=1)
    assert overlaps_window(a, b, FIXED_NOW - timedelta(minutes=30), FIXED_NOW + timedelta(minutes=30))
    assert not overlaps_window(a, b, b, b + timedelta(hours=1))
    assert not overlaps_window(a, b, a - timedelta(hours=2), a)


@pytest.mark.unit
def test_is_airing_at() -> None:
    start = FIXED_NOW
    stop = FIXED_NOW + timedelta(hours=1)
    assert is_airing_at(start, stop, FIXED_NOW)
    assert is_airing_at(start, stop, FIXED_NOW + timedelta(minutes=30))
    assert not is_airing_at(start, stop, stop)
    assert not is_airing_at(start, stop, start - timedelta(seconds=1))


@pytest.mark.unit
def test_matches_on_now_text_q_and_category() -> None:
    assert matches_on_now_text("Live Soccer", "Sports", q="soccer")
    assert matches_on_now_text("News", "Sports", q="sports")
    assert not matches_on_now_text("Cooking", "Lifestyle", q="soccer")
    assert matches_on_now_text("Match", "Sports", category_filter="sport")
    assert not matches_on_now_text("Match", "News", category_filter="sports")
    assert not matches_on_now_text("Soccer", "Sports")  # need q or category


@pytest.mark.unit
def test_epg_programme_schema() -> None:
    out = EpgProgrammeOut(
        id=1,
        channel_id="BBCOne.uk",
        start_at=FIXED_NOW,
        stop_at=FIXED_NOW + timedelta(hours=1),
        title="News",
        subtitle="",
        description="",
        category="News",
    )
    assert out.title == "News"
    assert out.channel_id == "BBCOne.uk"


@pytest.mark.unit
def test_epg_now_schema_nullable() -> None:
    resp = EpgNowResponse(channel_id="CNN.us", now=None, next=None)
    assert resp.now is None
    assert resp.next is None


@pytest.mark.unit
def test_epg_on_now_schema() -> None:
    prog = EpgProgrammeOut(
        id=2,
        channel_id="ESPN.us",
        start_at=FIXED_NOW,
        stop_at=FIXED_NOW + timedelta(hours=2),
        title="Soccer Live",
        category="Sports",
    )
    resp = EpgOnNowResponse(
        items=[EpgOnNowItem(channel_id="ESPN.us", programme=prog)],
        q="soccer",
        category=None,
    )
    assert len(resp.items) == 1
    assert resp.items[0].programme.title == "Soccer Live"


@pytest.mark.unit
def test_epg_schedule_schema() -> None:
    resp = EpgScheduleResponse(
        channel_id="BBCOne.uk",
        from_at=FIXED_NOW,
        to_at=FIXED_NOW + timedelta(hours=24),
        programmes=[],
    )
    assert resp.programmes == []


@pytest.mark.unit
def test_epg_programme_requires_id() -> None:
    with pytest.raises(ValidationError):
        EpgProgrammeOut(
            channel_id="x",
            start_at=FIXED_NOW,
            stop_at=FIXED_NOW + timedelta(hours=1),
            title="t",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_now_next_with_mocked_session() -> None:
    current = MagicMock()
    current.stop_at = FIXED_NOW + timedelta(hours=1)
    nxt = MagicMock()

    now_result = MagicMock()
    now_result.scalar_one_or_none.return_value = current
    next_result = MagicMock()
    next_result.scalar_one_or_none.return_value = nxt

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[now_result, next_result])

    got_now, got_next = await get_now_next(db, "BBCOne.uk", at=FIXED_NOW)
    assert got_now is current
    assert got_next is nxt
    assert db.execute.await_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_on_now_requires_filter() -> None:
    db = AsyncMock()
    with pytest.raises(ValueError, match="q or category"):
        await search_on_now(db)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_on_now_with_mocked_session() -> None:
    row = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [row]
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    rows = await search_on_now(db, q="soccer", at=FIXED_NOW, limit=10)
    assert rows == [row]
    db.execute.assert_awaited_once()
