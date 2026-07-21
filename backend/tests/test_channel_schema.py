"""Unit tests for channel and radio station schema coercion."""
from datetime import datetime, timezone

import pytest

from app.schemas import ChannelOut, RadioStationOut


class _OrmLike:
    """Minimal attribute bag mimicking SQLAlchemy model instances."""

    def __init__(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.mark.unit
def test_channel_out_coerces_none_optional_fields() -> None:
    orm = _OrmLike(
        id="test-1",
        name="Test Channel",
        alt_names=None,
        network=None,
        country_code=None,
        categories=None,
        is_nsfw=None,
        website=None,
        logo=None,
        stream_url=None,
        languages=None,
        health_status=None,
        health_checked_at=None,
        last_validated_at=None,
    )

    out = ChannelOut.model_validate(orm)

    assert out.alt_names == ""
    assert out.network == ""
    assert out.country_code == ""
    assert out.categories == ""
    assert out.website == ""
    assert out.logo == ""
    assert out.stream_url == ""
    assert out.languages == ""
    assert out.health_status == "unknown"
    assert out.health_checked_at == ""
    assert out.last_validated_at == ""
    assert out.is_nsfw is False


@pytest.mark.unit
def test_channel_out_coerces_datetime_timestamps() -> None:
    checked_at = datetime(2026, 4, 7, 12, 30, 45, tzinfo=timezone.utc)
    validated_at = datetime(2026, 4, 6, 8, 15, 0, tzinfo=timezone.utc)

    orm = _OrmLike(
        id="test-2",
        name="Timestamp Channel",
        health_checked_at=checked_at,
        last_validated_at=validated_at,
    )

    out = ChannelOut.model_validate(orm)

    assert out.health_checked_at == checked_at.isoformat()
    assert out.last_validated_at == validated_at.isoformat()


@pytest.mark.unit
def test_radio_station_out_coerces_none_numeric_and_timestamp_fields() -> None:
    checked_at = datetime(2026, 4, 7, 9, 0, 0, tzinfo=timezone.utc)

    orm = _OrmLike(
        id="radio-1",
        name="Test Radio",
        bitrate=None,
        votes=None,
        health_checked_at=checked_at,
        health_status=None,
        url=None,
    )

    out = RadioStationOut.model_validate(orm)

    assert out.bitrate == 0
    assert out.votes == 0
    assert out.health_checked_at == checked_at.isoformat()
    assert out.health_status == "unknown"
    assert out.url == ""
