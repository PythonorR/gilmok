from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.errors import bad_request, not_implemented
from app.routers.deps import PointQuery, category_param, owner_key, weights_param
from app.schemas.analysis import AnalysisResult, RecommendationsResponse
from app.schemas.common import ErrorBody
from app.schemas.locations import (
    CompareResponse,
    SavedLocationCreate,
    SavedLocationOut,
    SearchResponse,
)

ERRORS = {400: {"model": ErrorBody}, 422: {"model": ErrorBody}, 501: {"model": ErrorBody}}

router = APIRouter(prefix="/api", tags=["locations"], responses=ERRORS)


@router.get("/locations/search", response_model=SearchResponse)
def search(q: Annotated[str, Query(min_length=1, max_length=100)]) -> SearchResponse:
    """Address/place candidates via the Kakao Local API (server-side proxy, not persisted)."""
    raise not_implemented("locations.search")


@router.get("/locations/analyze", response_model=AnalysisResult)
def analyze(
    point: Annotated[PointQuery, Depends()],
    weights: Annotated[dict[str, float], Depends(weights_param)],
) -> AnalysisResult:
    raise not_implemented("locations.analyze")


@router.get("/locations/recommendations", response_model=RecommendationsResponse)
def recommendations(
    category: Annotated[str, Depends(category_param)],
    weights: Annotated[dict[str, float], Depends(weights_param)],
    bbox: str | None = None,
    district: Annotated[str | None, Query(pattern=r"^\d{5}$", description="시군구 코드")] = None,
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> RecommendationsResponse:
    if (bbox is None) == (district is None):
        raise bad_request("INVALID_AREA", "bbox와 district 중 하나만 지정해 주세요.")
    raise not_implemented("locations.recommendations")


@router.get("/locations/compare", response_model=CompareResponse)
def compare(
    ids: Annotated[str, Query(description="저장된 위치 id 2~3개, 쉼표 구분")],
    owner: Annotated[str, Depends(owner_key)],
) -> CompareResponse:
    try:
        parsed = [UUID(i) for i in ids.split(",")]
    except ValueError:
        raise bad_request("INVALID_IDS", "위치 id 형식이 올바르지 않습니다.") from None
    if not 2 <= len(set(parsed)) <= 3:
        raise bad_request("INVALID_IDS", "비교하려면 서로 다른 위치 2~3개를 선택해 주세요.")
    raise not_implemented("locations.compare")


@router.get("/saved-locations", response_model=list[SavedLocationOut])
def list_saved(owner: Annotated[str, Depends(owner_key)]) -> list[SavedLocationOut]:
    raise not_implemented("saved_locations.list")


@router.post("/saved-locations", response_model=SavedLocationOut, status_code=201)
def create_saved(
    body: SavedLocationCreate, owner: Annotated[str, Depends(owner_key)]
) -> SavedLocationOut:
    raise not_implemented("saved_locations.create")


@router.delete("/saved-locations/{location_id}", status_code=204)
def delete_saved(location_id: UUID, owner: Annotated[str, Depends(owner_key)]) -> None:
    raise not_implemented("saved_locations.delete")
