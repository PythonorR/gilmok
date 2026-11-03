from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

Resolution = Literal["point", "trade_area", "admin_dong", "district", "grid_250m", "grid_100m"]
ComponentKey = Literal["demand", "competition", "accessibility", "growth", "cost"]


class ErrorBody(BaseModel):
    code: str = Field(examples=["INVALID_RADIUS"])
    message: str = Field(examples=["분석 반경은 300m, 500m, 1km 중 하나여야 합니다."])
    details: object | None = None


class LatLng(BaseModel):
    lat: float
    lng: float


class SourceRef(BaseModel):
    """Provenance of the numbers in a response (one entry per dataset used)."""

    dataset_id: int
    key: str
    name: str
    provider: str
    resolution: Resolution
    period_start: date | None
    period_end: date | None
    fetched_at: datetime
    license_status: Literal["verified", "needs_verification"]
    is_synthetic: bool


class MissingIndicator(BaseModel):
    key: str  # component or metric key
    label: str  # Korean label, e.g. "임대료"
    reason: str  # Korean reason, e.g. "공개된 필지 단위 임대료 데이터 없음"


class Confidence(BaseModel):
    coverage: float = Field(ge=0, le=1, description="Sum of weights of available components")
    min_coverage: float = Field(ge=0, le=1)
    sufficient: bool
    missing: list[MissingIndicator]


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class Evidence(BaseModel):
    """One input value behind a score, traceable to its dataset and resolution."""

    metric_key: str
    label: str
    value: float | None
    unit: str  # '명', '개', 'm', '원', '%'
    resolution: Resolution
    dataset_id: int
    period: str | None
