"""Coordinate systems and distance helpers.

Storage CRS is EPSG:5179 (Korea 2000 / Unified CS, metres). API I/O is WGS84 (EPSG:4326).
Grid cells are aligned to the national standard grid: cell origins are multiples of the
cell size in EPSG:5179, which coincides with the 국가기준격자 lines for 100 m and 250 m cells.
"""

import math
from typing import Final

from pyproj import Geod, Transformer

SRID_WGS84: Final = 4326
SRID_METRIC: Final = 5179
EARTH_RADIUS_M: Final = 6_371_008.8  # mean Earth radius (IUGG)

_TO_METRIC = Transformer.from_crs(SRID_WGS84, SRID_METRIC, always_xy=True)
_TO_WGS84 = Transformer.from_crs(SRID_METRIC, SRID_WGS84, always_xy=True)
_GEOD = Geod(ellps="GRS80")


def to_metric(lng: float, lat: float) -> tuple[float, float]:
    """WGS84 (lng, lat) -> EPSG:5179 (x, y) in metres."""
    x, y = _TO_METRIC.transform(lng, lat)
    return float(x), float(y)


def to_wgs84(x: float, y: float) -> tuple[float, float]:
    """EPSG:5179 (x, y) -> WGS84 (lng, lat)."""
    lng, lat = _TO_WGS84.transform(x, y)
    return float(lng), float(lat)


def geodesic_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Ellipsoidal (GRS80) geodesic distance in metres. Reference for accuracy checks."""
    _, _, dist = _GEOD.inv(lng1, lat1, lng2, lat2)
    return float(dist)


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Spherical great-circle distance in metres. Fast; up to ~0.5% off the ellipsoid."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, a)))


def planar_distance_m(x1: float, y1: float, x2: float, y2: float) -> float:
    """Euclidean distance in a metric CRS (EPSG:5179)."""
    return math.hypot(x2 - x1, y2 - y1)


def circle_area_km2(radius_m: float) -> float:
    return math.pi * radius_m**2 / 1_000_000


def snap_to_grid(x: float, y: float, cell_size_m: int) -> tuple[int, int]:
    """Lower-left origin (EPSG:5179) of the grid cell that contains (x, y)."""
    if cell_size_m <= 0:
        raise ValueError("cell_size_m must be positive")
    return (
        int(math.floor(x / cell_size_m) * cell_size_m),
        int(math.floor(y / cell_size_m) * cell_size_m),
    )


def grid_cell_key(x: float, y: float, cell_size_m: int) -> str:
    """Deterministic internal key for a grid cell, e.g. '250:953000:1951250'.

    The official 국가지점번호 label format is recorded separately once verified (Step 2).
    """
    x0, y0 = snap_to_grid(x, y, cell_size_m)
    return f"{cell_size_m}:{x0}:{y0}"


def round_coord_for_cache(lat: float, lng: float, cell_m: int = 25) -> tuple[int, int]:
    """Snap a point to a 25 m metric grid so nearby clicks share a cache entry."""
    return snap_to_grid(*to_metric(lng, lat), cell_m)
