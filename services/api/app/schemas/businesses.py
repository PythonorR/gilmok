from pydantic import BaseModel

from app.schemas.common import LatLng, PageMeta, SourceRef


class NearbyBusiness(BaseModel):
    id: int
    name: str
    branch_name: str | None
    category_key: str | None
    category_code: str
    address: str | None
    location: LatLng
    distance_m: float


class CompetitionMetrics(BaseModel):
    """Explanatory metrics. Raw counts are not score inputs (see docs/scoring.md)."""

    competitor_count: int
    competitors_per_km2: float
    nearest_competitor_m: float | None
    mean_nearest_neighbor_m: float | None
    clark_evans_r: float | None  # <1 clustered, ~1 random, >1 dispersed; null if n < 3


class NearbyResponse(BaseModel):
    center: LatLng
    radius_m: int
    category: str
    metrics: CompetitionMetrics
    items: list[NearbyBusiness]
    meta: PageMeta
    sources: list[SourceRef]
    is_sample: bool
