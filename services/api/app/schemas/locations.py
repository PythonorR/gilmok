from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.analysis import AnalysisResult
from app.schemas.common import LatLng


class SearchCandidate(BaseModel):
    """Kakao Local result, proxied and never persisted."""

    name: str
    address: str | None
    road_address: str | None
    location: LatLng
    kind: str  # 'address' | 'place'


class SearchResponse(BaseModel):
    query: str
    items: list[SearchCandidate]


class SavedLocationCreate(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    lat: float
    lng: float
    radius_m: int
    category: str
    weights: str | None = None


class SavedLocationOut(BaseModel):
    id: UUID
    label: str
    location: LatLng
    radius_m: int
    category: str
    created_at: datetime
    snapshot: AnalysisResult  # frozen at save time


class CompareResponse(BaseModel):
    items: list[SavedLocationOut] = Field(min_length=2, max_length=3)
    tradeoffs: list[str]  # Korean; describes tradeoffs, never declares a universal winner
