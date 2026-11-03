from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import SourceRef


class DatasetStatus(SourceRef):
    last_run_status: Literal["running", "succeeded", "failed"] | None
    last_run_at: datetime | None
    row_count: int | None


class DatasetsStatusResponse(BaseModel):
    demo_mode: bool
    data_updated_at: datetime | None
    datasets: list[DatasetStatus]
