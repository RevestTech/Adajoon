"""Unit tests for radio geo_lat/geo_long sync mapping and schema coercion."""

import pytest

from app.schemas import RadioStationOut
from app.services.radio_service import _station_values_from_item


@pytest.mark.unit
def test_station_values_from_item_maps_geo_fields() -> None:
    item = {
        "stationuuid": "abc-123",
        "name": "Test FM",
        "url": "http://example.com/stream",
        "url_resolved": "http://example.com/stream.mp3",
        "homepage": "http://example.com",
        "favicon": "",
        "tags": "pop",
        "country": "United States",
        "countrycode": "us",
        "state": "NY",
        "language": "english",
        "codec": "MP3",
        "bitrate": 128,
        "votes": 42,
        "lastcheckok": 1,
        "geo_lat": 40.7128,
        "geo_long": -74.006,
    }

    values = _station_values_from_item(item)

    assert values is not None
    assert values["id"] == "abc-123"
    assert values["geo_lat"] == "40.7128"
    assert values["geo_long"] == "-74.006"
    assert values["country_code"] == "US"


@pytest.mark.unit
def test_station_values_from_item_coerces_missing_geo_to_empty() -> None:
    item = {
        "stationuuid": "no-geo",
        "name": "No Geo Station",
        "geo_lat": None,
    }

    values = _station_values_from_item(item)

    assert values is not None
    assert values["geo_lat"] == ""
    assert values["geo_long"] == ""


@pytest.mark.unit
def test_station_values_from_item_skips_missing_uuid() -> None:
    assert _station_values_from_item({"name": "orphan"}) is None


@pytest.mark.unit
def test_radio_station_out_coerces_none_and_float_geo() -> None:
    out_none = RadioStationOut.model_validate(
        {"id": "r1", "name": "A", "geo_lat": None, "geo_long": None}
    )
    assert out_none.geo_lat == ""
    assert out_none.geo_long == ""

    out_float = RadioStationOut.model_validate(
        {"id": "r2", "name": "B", "geo_lat": 51.5074, "geo_long": -0.1278}
    )
    assert out_float.geo_lat == "51.5074"
    assert out_float.geo_long == "-0.1278"
