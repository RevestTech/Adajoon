"""Unit tests for radio map bbox helpers, clustering, and schemas."""

import pytest
from pydantic import ValidationError

from app.schemas import MapBboxResponse, MapCluster, MapStationPin
from app.services.radio_service import (
    MAP_CLUSTER_ZOOM_MAX,
    cluster_points,
    grid_cell_degrees,
    parse_bbox,
    should_return_clusters,
)


@pytest.mark.unit
def test_parse_bbox_valid() -> None:
    west, south, east, north = parse_bbox("-74.1,40.6,-73.9,40.8")
    assert west == pytest.approx(-74.1)
    assert south == pytest.approx(40.6)
    assert east == pytest.approx(-73.9)
    assert north == pytest.approx(40.8)


@pytest.mark.unit
def test_parse_bbox_rejects_bad_shape() -> None:
    with pytest.raises(ValueError, match="west,south,east,north"):
        parse_bbox("1,2,3")


@pytest.mark.unit
def test_parse_bbox_rejects_inverted_lat() -> None:
    with pytest.raises(ValueError, match="south"):
        parse_bbox("0,10,1,5")


@pytest.mark.unit
def test_parse_bbox_clamps_out_of_range() -> None:
    west, south, east, north = parse_bbox("-200,-100,200,100")
    assert west == -180.0
    assert south == -90.0
    assert east == 180.0
    assert north == 90.0


@pytest.mark.unit
def test_grid_cell_degrees_shrinks_with_zoom() -> None:
    assert grid_cell_degrees(0) == 40.0
    assert grid_cell_degrees(2) == 10.0
    assert grid_cell_degrees(8) == 0.25  # floored by min cell
    assert grid_cell_degrees(5) < grid_cell_degrees(3)


@pytest.mark.unit
def test_should_return_clusters_threshold() -> None:
    assert should_return_clusters(0) is True
    assert should_return_clusters(MAP_CLUSTER_ZOOM_MAX) is True
    assert should_return_clusters(MAP_CLUSTER_ZOOM_MAX + 1) is False


@pytest.mark.unit
def test_cluster_points_buckets_nearby() -> None:
    # Same 1° cell for NYC pair; London in a separate cell.
    # Keep lngs away from integer boundaries (floor splits -74.01 vs -74.00).
    points = [
        (40.70, -74.20),
        (40.71, -74.25),
        (51.50, -0.12),
    ]
    clusters = cluster_points(points, cell_degrees=1.0)
    assert len(clusters) == 2
    by_count = sorted(clusters, key=lambda c: c.count, reverse=True)
    assert by_count[0].count == 2
    assert by_count[1].count == 1
    assert by_count[0].lat == pytest.approx(40.705)
    assert by_count[0].lng == pytest.approx(-74.225)


@pytest.mark.unit
def test_cluster_points_rejects_bad_cell() -> None:
    with pytest.raises(ValueError, match="cell_degrees"):
        cluster_points([(0.0, 0.0)], cell_degrees=0)


@pytest.mark.unit
def test_map_schemas_stations_response() -> None:
    resp = MapBboxResponse(
        type="stations",
        items=[
            MapStationPin(
                id="s1",
                name="NYC FM",
                favicon="https://example.com/i.png",
                geo_lat=40.7,
                geo_long=-74.0,
                country_code="US",
            )
        ],
        zoom=10,
    )
    assert resp.type == "stations"
    assert len(resp.items) == 1
    pin = resp.items[0]
    assert isinstance(pin, MapStationPin)
    assert pin.id == "s1"


@pytest.mark.unit
def test_map_schemas_clusters_response() -> None:
    resp = MapBboxResponse(
        type="clusters",
        items=[MapCluster(lat=40.7, lng=-74.0, count=12)],
        zoom=4,
    )
    assert resp.type == "clusters"
    assert resp.items[0].count == 12


@pytest.mark.unit
def test_map_cluster_requires_positive_count() -> None:
    with pytest.raises(ValidationError):
        MapCluster(lat=0.0, lng=0.0, count=0)
