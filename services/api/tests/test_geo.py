import math

import pytest

from app.core.geo import (
    circle_area_km2,
    geodesic_m,
    grid_cell_key,
    haversine_m,
    planar_distance_m,
    round_coord_for_cache,
    snap_to_grid,
    to_metric,
    to_wgs84,
)

# Reference points (WGS84)
CITY_HALL = (37.5662952, 126.9779451)  # 서울시청
HONGIK_STN = (37.557527, 126.9244669)  # 홍대입구역


def test_epsg5179_false_origin():
    # EPSG:5179 has its origin at 38N 127.5E with false easting/northing 1,000,000 / 2,000,000.
    x, y = to_metric(127.5, 38.0)
    assert x == pytest.approx(1_000_000, abs=0.01)
    assert y == pytest.approx(2_000_000, abs=0.01)


def test_seoul_lands_in_national_grid_square_dasa():
    # Seoul lies in 100 km square '다사': x in [900 km, 1000 km), y in [1900 km, 2000 km).
    x, y = to_metric(CITY_HALL[1], CITY_HALL[0])
    assert 900_000 <= x < 1_000_000
    assert 1_900_000 <= y < 2_000_000


def test_round_trip_is_sub_millimetre():
    lat, lng = HONGIK_STN
    lng2, lat2 = to_wgs84(*to_metric(lng, lat))
    assert haversine_m(lat, lng, lat2, lng2) < 0.001


def test_haversine_zero_and_symmetry():
    assert haversine_m(*CITY_HALL, *CITY_HALL) == 0
    assert haversine_m(*CITY_HALL, *HONGIK_STN) == pytest.approx(
        haversine_m(*HONGIK_STN, *CITY_HALL)
    )


def test_haversine_one_degree_latitude():
    # One degree of latitude on the mean-radius sphere is ~111.195 km.
    assert haversine_m(37.0, 127.0, 38.0, 127.0) == pytest.approx(111_195, rel=1e-4)


def test_projected_distance_matches_geodesic_in_seoul():
    # City Hall -> Hongik Univ. Stn is roughly 4.8 km. EPSG:5179 planar distance (what PostGIS
    # ST_Distance/ST_DWithin use on our columns) must match the ellipsoidal geodesic within 0.1%.
    # Seoul is ~0.5 deg west of the 127.5E central meridian, so TM scale error is ~0.04%.
    d_geo = geodesic_m(*CITY_HALL, *HONGIK_STN)
    x1, y1 = to_metric(CITY_HALL[1], CITY_HALL[0])
    x2, y2 = to_metric(HONGIK_STN[1], HONGIK_STN[0])
    assert 4_500 < d_geo < 5_200
    assert planar_distance_m(x1, y1, x2, y2) == pytest.approx(d_geo, rel=1e-3)


def test_haversine_within_half_percent_of_geodesic():
    assert haversine_m(*CITY_HALL, *HONGIK_STN) == pytest.approx(
        geodesic_m(*CITY_HALL, *HONGIK_STN), rel=5e-3
    )


def test_planar_distance_pythagoras():
    assert planar_distance_m(0, 0, 300, 400) == 500


@pytest.mark.parametrize(("radius", "expected"), [(300, 0.2827), (500, 0.7854), (1000, 3.1416)])
def test_circle_area(radius, expected):
    assert circle_area_km2(radius) == pytest.approx(expected, rel=1e-3)


def test_snap_to_grid_aligns_to_cell_multiples():
    assert snap_to_grid(953_123.4, 1_951_999.9, 250) == (953_000, 1_951_750)
    assert snap_to_grid(953_123.4, 1_951_999.9, 100) == (953_100, 1_951_900)
    # Points on a cell boundary belong to the cell to their upper-right.
    assert snap_to_grid(953_250, 1_951_250, 250) == (953_250, 1_951_250)


def test_100m_cells_nest_inside_250m_cells_on_500m_boundaries():
    # 100 and 250 share boundaries every 500 m (their LCM), so nesting holds at those lines.
    for v in (953_000.0, 953_500.0):
        assert snap_to_grid(v, v, 100)[0] == snap_to_grid(v, v, 250)[0]


def test_snap_to_grid_rejects_bad_size():
    with pytest.raises(ValueError):
        snap_to_grid(1, 1, 0)


def test_grid_cell_key_is_deterministic():
    assert grid_cell_key(953_123.4, 1_951_999.9, 250) == "250:953000:1951750"


def test_cache_rounding_groups_nearby_points():
    lat, lng = HONGIK_STN
    # Points a few metres apart usually share a key; points 100 m apart never do.
    far = round_coord_for_cache(lat + 0.0009, lng)  # ~100 m north
    assert round_coord_for_cache(lat, lng) != far
    k = round_coord_for_cache(lat, lng)
    assert all(isinstance(v, int) and v % 25 == 0 for v in k)
    assert not math.isnan(k[0])
