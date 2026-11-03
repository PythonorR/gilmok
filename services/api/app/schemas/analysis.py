from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ComponentKey, Confidence, Evidence, LatLng, SourceRef


class ComponentScore(BaseModel):
    key: ComponentKey
    label: str
    score: float | None = Field(
        None, ge=0, le=100, description="Percentile vs. Seoul; null = missing"
    )
    weight: float = Field(ge=0, le=1)
    evidence: list[Evidence]


class TradeAreaRef(BaseModel):
    id: int
    code: str
    name: str
    area_type: str | None


class Risk(BaseModel):
    key: str
    severity: Literal["info", "caution", "warning"]
    message: str  # Korean


class AnalysisResult(BaseModel):
    """Response of /api/locations/analyze. `total` is a relative composite, not a probability."""

    location: LatLng
    radius_m: int
    category: str
    trade_area: TradeAreaRef | None
    status: Literal["scored", "insufficient_data"]
    total: float | None = Field(None, ge=0, le=100)
    components: list[ComponentScore]
    risks: list[Risk]
    explanation: list[str]  # rule-based Korean sentences built only from the fields above
    confidence: Confidence
    sources: list[SourceRef]
    config_version: str
    data_version: str
    is_sample: bool


class Recommendation(BaseModel):
    rank: int
    cell_id: int
    location: LatLng
    trade_area: TradeAreaRef | None
    total: float = Field(ge=0, le=100)
    components: list[ComponentScore]
    reasons: list[str]
    risks: list[Risk]
    confidence: Confidence


class RecommendationsResponse(BaseModel):
    category: str
    items: list[Recommendation]
    sources: list[SourceRef]
    config_version: str
    data_version: str
    is_sample: bool
