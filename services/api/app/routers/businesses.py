from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.errors import not_implemented
from app.routers.deps import PointQuery
from app.routers.locations import ERRORS
from app.schemas.businesses import NearbyResponse

router = APIRouter(prefix="/api/businesses", tags=["businesses"], responses=ERRORS)


@router.get("/nearby", response_model=NearbyResponse)
def nearby(
    point: Annotated[PointQuery, Depends()],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> NearbyResponse:
    raise not_implemented("businesses.nearby")
