from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_session
from app.models import Dataset, EtlRun
from app.schemas.datasets import DatasetsStatusResponse, DatasetStatus

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("/status", response_model=DatasetsStatusResponse)
def status(db: Annotated[Session, Depends(get_session)]) -> DatasetsStatusResponse:
    """Latest version of each dataset with its provenance and last ETL run."""
    latest = select(Dataset).distinct(Dataset.key).order_by(Dataset.key, Dataset.fetched_at.desc())
    items: list[DatasetStatus] = []
    for ds in db.scalars(latest):
        run = db.scalars(
            select(EtlRun)
            .where(EtlRun.dataset_id == ds.id)
            .order_by(EtlRun.started_at.desc())
            .limit(1)
        ).first()
        items.append(
            DatasetStatus(
                dataset_id=ds.id,
                key=ds.key,
                name=ds.name,
                provider=ds.provider,
                resolution=ds.resolution,
                period_start=ds.period_start,
                period_end=ds.period_end,
                fetched_at=ds.fetched_at,
                license_status=ds.license_status,
                is_synthetic=ds.is_synthetic,
                last_run_status=run.status if run else None,
                last_run_at=run.finished_at or run.started_at if run else None,
                row_count=run.rows_out if run else None,
            )
        )
    updated = db.scalar(select(func.max(Dataset.fetched_at)))
    return DatasetsStatusResponse(
        demo_mode=get_settings().demo_mode, data_updated_at=updated, datasets=items
    )
