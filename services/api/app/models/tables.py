"""Core tables.

Provenance rule: every data-bearing table references `datasets.id`, so the source,
resolution, reporting period and fetch time of any number are always traceable.
"""

import uuid
from datetime import date, datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.geo import SRID_METRIC
from app.models.base import Base, CreatedAtMixin

# GIST indexes are declared explicitly in __table_args__, so GeoAlchemy2's implicit one is off.
POINT = Geometry("POINT", srid=SRID_METRIC, spatial_index=False)
POLYGON = Geometry("POLYGON", srid=SRID_METRIC, spatial_index=False)
MULTIPOLYGON = Geometry("MULTIPOLYGON", srid=SRID_METRIC, spatial_index=False)


def gist(table: str, column: str = "geom") -> Index:
    return Index(f"ix_{table}_{column}_gist", column, postgresql_using="gist")


# --- Provenance -----------------------------------------------------------------------


class Dataset(CreatedAtMixin, Base):
    """One ingested version of an external dataset (a new fetch = a new row)."""

    __tablename__ = "datasets"
    __table_args__ = (
        UniqueConstraint("key", "checksum"),
        CheckConstraint(
            "resolution IN ('point','trade_area','admin_dong','district','grid_250m','grid_100m')",
            name="resolution",
        ),
        CheckConstraint(
            "license_status IN ('verified','needs_verification')", name="license_status"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), index=True)  # e.g. 'semas_stores'
    name: Mapped[str] = mapped_column(String(200))  # Korean display name
    provider: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str] = mapped_column(Text)
    license_note: Mapped[str] = mapped_column(Text, default="")
    license_status: Mapped[str] = mapped_column(String(32), default="needs_verification")
    resolution: Mapped[str] = mapped_column(String(32))
    coverage: Mapped[str] = mapped_column(String(200))  # e.g. '서울특별시 전체'
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    checksum: Mapped[str] = mapped_column(String(64))  # sha256 of the raw payload
    # Synthetic demo data is flagged at the source, so it can never pass as real analysis.
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)


class EtlRun(Base):
    __tablename__ = "etl_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline: Mapped[str] = mapped_column(String(64), index=True)
    dataset_id: Mapped[int | None] = mapped_column(ForeignKey("datasets.id"))
    status: Mapped[str] = mapped_column(String(16))  # running | succeeded | failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rows_in: Mapped[int | None] = mapped_column(Integer)
    rows_out: Mapped[int | None] = mapped_column(Integer)
    message: Mapped[str | None] = mapped_column(Text)


# --- Categories -----------------------------------------------------------------------


class Category(Base):
    """Internal business category (e.g. 'cafe'). Adding one is a data change, not code."""

    __tablename__ = "categories"

    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    name_ko: Mapped[str] = mapped_column(String(64))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class CategoryMap(Base):
    """Maps a source system's classification code to an internal category."""

    __tablename__ = "category_map"

    source_system: Mapped[str] = mapped_column(String(32), primary_key=True)  # 'semas', 'golmok'
    source_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    category_key: Mapped[str] = mapped_column(ForeignKey("categories.key"), index=True)
    mapping_note: Mapped[str] = mapped_column(Text, default="")


# --- Point and area data --------------------------------------------------------------


class Business(Base):
    __tablename__ = "businesses"
    __table_args__ = (
        UniqueConstraint("dataset_id", "source_store_id"),
        Index("ix_businesses_category_key_dataset_id", "category_key", "dataset_id"),
        gist("businesses"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_store_id: Mapped[str] = mapped_column(String(64))
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    branch_name: Mapped[str | None] = mapped_column(String(200))
    category_code: Mapped[str] = mapped_column(String(32))  # source classification code
    category_key: Mapped[str | None] = mapped_column(ForeignKey("categories.key"))
    address: Mapped[str | None] = mapped_column(Text)
    geom: Mapped[Any] = mapped_column(POINT)


class TradeArea(Base):
    """A Seoul trade-area (상권) polygon. Demand metrics live at this resolution."""

    __tablename__ = "trade_areas"
    __table_args__ = (UniqueConstraint("dataset_id", "code"), gist("trade_areas"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(200))
    area_type: Mapped[str | None] = mapped_column(String(32))  # 골목상권, 발달상권, ...
    district_code: Mapped[str | None] = mapped_column(String(16), index=True)
    geom: Mapped[Any] = mapped_column(MULTIPOLYGON)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))


class TradeAreaMetric(Base):
    """Long-format trade-area metric. category_key is NULL for category-independent metrics."""

    __tablename__ = "trade_area_metrics"
    __table_args__ = (
        UniqueConstraint(
            "trade_area_id",
            "metric_key",
            "category_key",
            "period",
            "dataset_id",
            name="uq_trade_area_metrics_natural_key",
            postgresql_nulls_not_distinct=True,
        ),
        Index("ix_trade_area_metrics_lookup", "metric_key", "category_key", "period"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trade_area_id: Mapped[int] = mapped_column(ForeignKey("trade_areas.id", ondelete="CASCADE"))
    metric_key: Mapped[str] = mapped_column(String(64))  # e.g. 'floating_pop', 'est_sales'
    category_key: Mapped[str | None] = mapped_column(ForeignKey("categories.key"))
    period: Mapped[str] = mapped_column(String(16))  # e.g. '2026Q2'
    value: Mapped[float | None] = mapped_column(Double)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))


class Poi(Base):
    """Demand generators and transit: stations, bus stops, schools, offices, attractions."""

    __tablename__ = "pois"
    __table_args__ = (Index("ix_pois_kind", "kind"), gist("pois"))

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(200))
    source_id: Mapped[str | None] = mapped_column(String(64))
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    geom: Mapped[Any] = mapped_column(POINT)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))


# --- Grid and scoring -----------------------------------------------------------------


class GridCell(Base):
    """Analysis cell aligned to the national standard grid (EPSG:5179 multiples of size)."""

    __tablename__ = "grid_cells"
    __table_args__ = (
        UniqueConstraint("cell_size_m", "cell_key"),
        CheckConstraint("cell_size_m IN (100, 250)", name="cell_size"),
        gist("grid_cells"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cell_size_m: Mapped[int] = mapped_column(Integer)
    cell_key: Mapped[str] = mapped_column(String(48))  # see app.core.geo.grid_cell_key
    national_grid_id: Mapped[str | None] = mapped_column(String(32))  # 국가지점번호, if verified
    district_code: Mapped[str | None] = mapped_column(String(16), index=True)
    # Trade area that contains the cell centroid; NULL = outside every trade area.
    trade_area_id: Mapped[int | None] = mapped_column(ForeignKey("trade_areas.id"), index=True)
    geom: Mapped[Any] = mapped_column(POLYGON)


class ScoreConfig(CreatedAtMixin, Base):
    __tablename__ = "score_configs"
    __table_args__ = (UniqueConstraint("category_key", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_key: Mapped[str] = mapped_column(ForeignKey("categories.key"))
    version: Mapped[str] = mapped_column(String(32))
    weights: Mapped[dict[str, float]] = mapped_column(JSONB)
    min_coverage: Mapped[float] = mapped_column(Double, default=0.70)
    # Component definitions: which metrics feed each component, and their direction.
    definition: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str] = mapped_column(Text, default="")


class ScoreBaseline(Base):
    """Seoul-wide distribution of a metric, used for percentile normalisation."""

    __tablename__ = "score_baselines"
    __table_args__ = (UniqueConstraint("metric_key", "category_key", "data_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_key: Mapped[str] = mapped_column(String(64))
    category_key: Mapped[str | None] = mapped_column(ForeignKey("categories.key"))
    data_version: Mapped[str] = mapped_column(String(64))
    higher_is_better: Mapped[bool] = mapped_column(Boolean)
    sample_size: Mapped[int] = mapped_column(Integer)
    sorted_values: Mapped[list[float]] = mapped_column(JSONB)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class GridScore(Base):
    __tablename__ = "grid_scores"
    __table_args__ = (
        UniqueConstraint("cell_id", "config_id", "data_version"),
        CheckConstraint("coverage >= 0 AND coverage <= 1", name="coverage_range"),
        CheckConstraint("total IS NULL OR (total >= 0 AND total <= 100)", name="total_range"),
        CheckConstraint("status IN ('scored','insufficient_data')", name="status"),
        Index("ix_grid_scores_config_id_data_version", "config_id", "data_version"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cell_id: Mapped[int] = mapped_column(ForeignKey("grid_cells.id", ondelete="CASCADE"))
    config_id: Mapped[int] = mapped_column(ForeignKey("score_configs.id", ondelete="CASCADE"))
    components: Mapped[dict[str, Any]] = mapped_column(JSONB)  # {key: score|null, ...}
    total: Mapped[float | None] = mapped_column(Double)  # NULL when status = insufficient_data
    coverage: Mapped[float] = mapped_column(Double)
    status: Mapped[str] = mapped_column(String(24))
    missing: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)  # [{key, reason}]
    data_version: Mapped[str] = mapped_column(String(64))  # hash of data_versions
    data_versions: Mapped[dict[str, int]] = mapped_column(JSONB)  # {dataset_key: dataset_id}
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- User data ------------------------------------------------------------------------


class SavedLocation(CreatedAtMixin, Base):
    """Saved candidate. The analysis snapshot is frozen at save time."""

    __tablename__ = "saved_locations"
    __table_args__ = (
        CheckConstraint("radius_m IN (300, 500, 1000)", name="radius"),
        gist("saved_locations"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_key: Mapped[str] = mapped_column(String(64), index=True)  # anonymous session key
    label: Mapped[str] = mapped_column(String(100))
    geom: Mapped[Any] = mapped_column(POINT)
    radius_m: Mapped[int] = mapped_column(Integer)
    category_key: Mapped[str] = mapped_column(ForeignKey("categories.key"))
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)


class ResponseCache(Base):
    """Analysis response cache. Key includes the data version, so new data never hits stale."""

    __tablename__ = "response_cache"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)  # sha256 of the key parts
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    data_version: Mapped[str] = mapped_column(String(64), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
