from typing import Literal

from pydantic import BaseModel

from app.schemas.common import ComponentKey, SourceRef


class CellProperties(BaseModel):
    cell_id: int
    status: Literal["scored", "insufficient_data"]
    band: Literal["favorable", "moderate", "unfavorable", "no_data"]
    total: float | None
    coverage: float
    components: dict[ComponentKey, float | None]
    reason: str | None  # Korean reason for gray cells


class CellFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict  # GeoJSON Polygon in WGS84
    properties: CellProperties


class HeatmapResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[CellFeature]
    cell_size_m: int
    category: str
    config_version: str
    data_version: str
    sources: list[SourceRef]
    is_sample: bool
