"""Validation of common query parameters shared by several endpoints."""

import math
from dataclasses import dataclass
from typing import Final, Literal

from pyproj import Geod

from app.core.errors import bad_request

ALLOWED_RADII_M: Final = (300, 500, 1000)
ALLOWED_CELL_SIZES_M: Final = (100, 250)
COMPONENT_KEYS: Final = ("demand", "competition", "accessibility", "growth", "cost")
ComponentKey = Literal["demand", "competition", "accessibility", "growth", "cost"]

# Rough bounding box of South Korea; rejects swapped or garbage coordinates early.
KOREA_BOUNDS: Final = {"min_lat": 33.0, "max_lat": 38.7, "min_lng": 124.5, "max_lng": 132.0}

_GEOD = Geod(ellps="WGS84")


def validate_point(lat: float, lng: float) -> None:
    b = KOREA_BOUNDS
    if not (b["min_lat"] <= lat <= b["max_lat"] and b["min_lng"] <= lng <= b["max_lng"]):
        raise bad_request(
            "OUT_OF_BOUNDS",
            "대한민국 범위 밖의 좌표입니다.",
            {"lat": lat, "lng": lng},
        )


def validate_radius(radius: int) -> int:
    if radius not in ALLOWED_RADII_M:
        raise bad_request(
            "INVALID_RADIUS",
            "분석 반경은 300m, 500m, 1km 중 하나여야 합니다.",
            {"allowed": list(ALLOWED_RADII_M), "received": radius},
        )
    return radius


def validate_cell_size(cell_size: int) -> int:
    if cell_size not in ALLOWED_CELL_SIZES_M:
        raise bad_request(
            "INVALID_CELL_SIZE",
            "격자 크기는 100m 또는 250m여야 합니다.",
            {"allowed": list(ALLOWED_CELL_SIZES_M), "received": cell_size},
        )
    return cell_size


def validate_category(category: str, enabled: tuple[str, ...]) -> str:
    if category not in enabled:
        raise bad_request(
            "UNSUPPORTED_CATEGORY",
            "아직 지원하지 않는 업종입니다.",
            {"supported": list(enabled), "received": category},
        )
    return category


@dataclass(frozen=True)
class BBox:
    min_lng: float
    min_lat: float
    max_lng: float
    max_lat: float

    @property
    def area_km2(self) -> float:
        lngs = [self.min_lng, self.max_lng, self.max_lng, self.min_lng]
        lats = [self.min_lat, self.min_lat, self.max_lat, self.max_lat]
        area_m2, _ = _GEOD.polygon_area_perimeter(lngs, lats)
        return abs(area_m2) / 1_000_000


def parse_bbox(raw: str, max_area_km2: float) -> BBox:
    """Parse 'minLng,minLat,maxLng,maxLat' and enforce a maximum area."""
    try:
        parts = [float(p) for p in raw.split(",")]
    except ValueError:
        parts = []
    if len(parts) != 4:
        raise bad_request(
            "INVALID_BBOX",
            "지도 범위 형식이 올바르지 않습니다. (minLng,minLat,maxLng,maxLat)",
            {"received": raw},
        )
    bbox = BBox(*parts)
    if bbox.min_lng >= bbox.max_lng or bbox.min_lat >= bbox.max_lat:
        raise bad_request(
            "INVALID_BBOX", "지도 범위의 최솟값이 최댓값보다 커야 합니다.", {"received": raw}
        )
    validate_point(bbox.min_lat, bbox.min_lng)
    validate_point(bbox.max_lat, bbox.max_lng)
    if bbox.area_km2 > max_area_km2:
        raise bad_request(
            "BBOX_TOO_LARGE",
            "요청한 지도 범위가 너무 넓습니다. 지도를 확대해 주세요.",
            {"area_km2": round(bbox.area_km2, 2), "max_area_km2": max_area_km2},
        )
    return bbox


def parse_weights(raw: str | None, defaults: dict[str, float]) -> dict[str, float]:
    """Parse 'demand:0.35,competition:0.25,...'.

    Omitted components keep their default weight. Weights must be non-negative, and the
    result is normalised to sum to 1 so that coverage stays on a 0–1 scale.
    """
    weights = dict(defaults)
    if raw:
        for item in raw.split(","):
            key, sep, val = item.partition(":")
            key = key.strip()
            if not sep or key not in COMPONENT_KEYS:
                raise bad_request(
                    "INVALID_WEIGHTS",
                    "가중치 형식이 올바르지 않습니다.",
                    {"item": item, "allowed_keys": list(COMPONENT_KEYS)},
                )
            try:
                w = float(val)
            except ValueError:
                raise bad_request(
                    "INVALID_WEIGHTS", "가중치는 숫자여야 합니다.", {"item": item}
                ) from None
            if not math.isfinite(w) or w < 0:
                raise bad_request(
                    "INVALID_WEIGHTS", "가중치는 0 이상이어야 합니다.", {"item": item}
                )
            weights[key] = w
    total = sum(weights.values())
    if total <= 0:
        raise bad_request(
            "INVALID_WEIGHTS", "가중치 합계는 0보다 커야 합니다.", {"weights": weights}
        )
    return {k: weights[k] / total for k in COMPONENT_KEYS if k in weights}


def weights_cache_token(weights: dict[str, float]) -> str:
    return ",".join(f"{k}:{weights.get(k, 0):.4f}" for k in COMPONENT_KEYS)
