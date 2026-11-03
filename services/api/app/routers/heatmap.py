from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.errors import not_implemented
from app.core.params import BBox, validate_cell_size
from app.routers.deps import bbox_param, category_param, weights_param
from app.routers.locations import ERRORS
from app.schemas.heatmap import HeatmapResponse

router = APIRouter(prefix="/api", tags=["heatmap"], responses=ERRORS)


@router.get("/heatmap", response_model=HeatmapResponse)
def heatmap(
    bbox: Annotated[BBox, Depends(bbox_param)],
    category: Annotated[str, Depends(category_param)],
    weights: Annotated[dict[str, float], Depends(weights_param)],
    cell_size: Annotated[int, Query()] = 250,
) -> HeatmapResponse:
    """Precomputed grid scores only — never computed on request."""
    validate_cell_size(cell_size)
    raise not_implemented("heatmap")
