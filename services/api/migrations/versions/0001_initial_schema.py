"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-11-03 20:53:03.776276
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "categories",
        sa.Column("key", sa.String(length=32), nullable=False),
        sa.Column("name_ko", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_categories")),
    )
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("provider", sa.String(length=200), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("license_note", sa.Text(), nullable=False),
        sa.Column("license_status", sa.String(length=32), nullable=False),
        sa.Column("resolution", sa.String(length=32), nullable=False),
        sa.Column("coverage", sa.String(length=200), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "license_status IN ('verified','needs_verification')",
            name=op.f("ck_datasets_license_status"),
        ),
        sa.CheckConstraint(
            "resolution IN ('point','trade_area','admin_dong','district','grid_250m','grid_100m')",
            name=op.f("ck_datasets_resolution"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_datasets")),
        sa.UniqueConstraint("key", "checksum", name=op.f("uq_datasets_key_checksum")),
    )
    op.create_index(op.f("ix_datasets_key"), "datasets", ["key"], unique=False)
    op.create_table(
        "response_cache",
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("data_version", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_response_cache")),
    )
    op.create_index(
        op.f("ix_response_cache_data_version"), "response_cache", ["data_version"], unique=False
    )
    op.create_index(
        op.f("ix_response_cache_expires_at"), "response_cache", ["expires_at"], unique=False
    )
    op.create_geospatial_table(
        "businesses",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("source_store_id", sa.String(length=64), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("branch_name", sa.String(length=200), nullable=True),
        sa.Column("category_code", sa.String(length=32), nullable=False),
        sa.Column("category_key", sa.String(length=32), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column(
            "geom",
            Geometry(
                geometry_type="POINT",
                srid=5179,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["category_key"], ["categories.key"], name=op.f("fk_businesses_category_key_categories")
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name=op.f("fk_businesses_dataset_id_datasets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_businesses")),
        sa.UniqueConstraint(
            "dataset_id", "source_store_id", name=op.f("uq_businesses_dataset_id_source_store_id")
        ),
    )
    op.create_index(
        "ix_businesses_category_key_dataset_id",
        "businesses",
        ["category_key", "dataset_id"],
        unique=False,
    )
    op.create_geospatial_index(
        "ix_businesses_geom_gist",
        "businesses",
        ["geom"],
        unique=False,
        postgresql_using="gist",
        postgresql_ops={},
    )
    op.create_table(
        "category_map",
        sa.Column("source_system", sa.String(length=32), nullable=False),
        sa.Column("source_code", sa.String(length=32), nullable=False),
        sa.Column("category_key", sa.String(length=32), nullable=False),
        sa.Column("mapping_note", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_key"],
            ["categories.key"],
            name=op.f("fk_category_map_category_key_categories"),
        ),
        sa.PrimaryKeyConstraint("source_system", "source_code", name=op.f("pk_category_map")),
    )
    op.create_index(
        op.f("ix_category_map_category_key"), "category_map", ["category_key"], unique=False
    )
    op.create_table(
        "etl_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pipeline", sa.String(length=64), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rows_in", sa.Integer(), nullable=True),
        sa.Column("rows_out", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["dataset_id"], ["datasets.id"], name=op.f("fk_etl_runs_dataset_id_datasets")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_etl_runs")),
    )
    op.create_index(op.f("ix_etl_runs_pipeline"), "etl_runs", ["pipeline"], unique=False)
    op.create_geospatial_table(
        "pois",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "geom",
            Geometry(
                geometry_type="POINT",
                srid=5179,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name=op.f("fk_pois_dataset_id_datasets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pois")),
    )
    op.create_geospatial_index(
        "ix_pois_geom_gist",
        "pois",
        ["geom"],
        unique=False,
        postgresql_using="gist",
        postgresql_ops={},
    )
    op.create_index("ix_pois_kind", "pois", ["kind"], unique=False)
    op.create_geospatial_table(
        "saved_locations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column(
            "geom",
            Geometry(
                geometry_type="POINT",
                srid=5179,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.Column("radius_m", sa.Integer(), nullable=False),
        sa.Column("category_key", sa.String(length=32), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("radius_m IN (300, 500, 1000)", name=op.f("ck_saved_locations_radius")),
        sa.ForeignKeyConstraint(
            ["category_key"],
            ["categories.key"],
            name=op.f("fk_saved_locations_category_key_categories"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_saved_locations")),
    )
    op.create_geospatial_index(
        "ix_saved_locations_geom_gist",
        "saved_locations",
        ["geom"],
        unique=False,
        postgresql_using="gist",
        postgresql_ops={},
    )
    op.create_index(
        op.f("ix_saved_locations_owner_key"), "saved_locations", ["owner_key"], unique=False
    )
    op.create_table(
        "score_baselines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("metric_key", sa.String(length=64), nullable=False),
        sa.Column("category_key", sa.String(length=32), nullable=True),
        sa.Column("data_version", sa.String(length=64), nullable=False),
        sa.Column("higher_is_better", sa.Boolean(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("sorted_values", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["category_key"],
            ["categories.key"],
            name=op.f("fk_score_baselines_category_key_categories"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_score_baselines")),
        sa.UniqueConstraint(
            "metric_key",
            "category_key",
            "data_version",
            name=op.f("uq_score_baselines_metric_key_category_key_data_version"),
        ),
    )
    op.create_table(
        "score_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_key", sa.String(length=32), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("weights", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("min_coverage", sa.Double(), nullable=False),
        sa.Column("definition", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["category_key"],
            ["categories.key"],
            name=op.f("fk_score_configs_category_key_categories"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_score_configs")),
        sa.UniqueConstraint(
            "category_key", "version", name=op.f("uq_score_configs_category_key_version")
        ),
    )
    op.create_geospatial_table(
        "trade_areas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("area_type", sa.String(length=32), nullable=True),
        sa.Column("district_code", sa.String(length=16), nullable=True),
        sa.Column(
            "geom",
            Geometry(
                geometry_type="MULTIPOLYGON",
                srid=5179,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name=op.f("fk_trade_areas_dataset_id_datasets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trade_areas")),
        sa.UniqueConstraint("dataset_id", "code", name=op.f("uq_trade_areas_dataset_id_code")),
    )
    op.create_index(
        op.f("ix_trade_areas_district_code"), "trade_areas", ["district_code"], unique=False
    )
    op.create_geospatial_index(
        "ix_trade_areas_geom_gist",
        "trade_areas",
        ["geom"],
        unique=False,
        postgresql_using="gist",
        postgresql_ops={},
    )
    op.create_geospatial_table(
        "grid_cells",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("cell_size_m", sa.Integer(), nullable=False),
        sa.Column("cell_key", sa.String(length=48), nullable=False),
        sa.Column("national_grid_id", sa.String(length=32), nullable=True),
        sa.Column("district_code", sa.String(length=16), nullable=True),
        sa.Column("trade_area_id", sa.Integer(), nullable=True),
        sa.Column(
            "geom",
            Geometry(
                geometry_type="POLYGON",
                srid=5179,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.CheckConstraint("cell_size_m IN (100, 250)", name=op.f("ck_grid_cells_cell_size")),
        sa.ForeignKeyConstraint(
            ["trade_area_id"],
            ["trade_areas.id"],
            name=op.f("fk_grid_cells_trade_area_id_trade_areas"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grid_cells")),
        sa.UniqueConstraint(
            "cell_size_m", "cell_key", name=op.f("uq_grid_cells_cell_size_m_cell_key")
        ),
    )
    op.create_index(
        op.f("ix_grid_cells_district_code"), "grid_cells", ["district_code"], unique=False
    )
    op.create_geospatial_index(
        "ix_grid_cells_geom_gist",
        "grid_cells",
        ["geom"],
        unique=False,
        postgresql_using="gist",
        postgresql_ops={},
    )
    op.create_index(
        op.f("ix_grid_cells_trade_area_id"), "grid_cells", ["trade_area_id"], unique=False
    )
    op.create_table(
        "trade_area_metrics",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("trade_area_id", sa.Integer(), nullable=False),
        sa.Column("metric_key", sa.String(length=64), nullable=False),
        sa.Column("category_key", sa.String(length=32), nullable=True),
        sa.Column("period", sa.String(length=16), nullable=False),
        sa.Column("value", sa.Double(), nullable=True),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_key"],
            ["categories.key"],
            name=op.f("fk_trade_area_metrics_category_key_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name=op.f("fk_trade_area_metrics_dataset_id_datasets"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["trade_area_id"],
            ["trade_areas.id"],
            name=op.f("fk_trade_area_metrics_trade_area_id_trade_areas"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trade_area_metrics")),
        sa.UniqueConstraint(
            "trade_area_id",
            "metric_key",
            "category_key",
            "period",
            "dataset_id",
            name="uq_trade_area_metrics_natural_key",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(
        "ix_trade_area_metrics_lookup",
        "trade_area_metrics",
        ["metric_key", "category_key", "period"],
        unique=False,
    )
    op.create_table(
        "grid_scores",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("cell_id", sa.BigInteger(), nullable=False),
        sa.Column("config_id", sa.Integer(), nullable=False),
        sa.Column("components", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("total", sa.Double(), nullable=True),
        sa.Column("coverage", sa.Double(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("missing", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("data_version", sa.String(length=64), nullable=False),
        sa.Column("data_versions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('scored','insufficient_data')", name=op.f("ck_grid_scores_status")
        ),
        sa.CheckConstraint(
            "coverage >= 0 AND coverage <= 1", name=op.f("ck_grid_scores_coverage_range")
        ),
        sa.CheckConstraint(
            "total IS NULL OR (total >= 0 AND total <= 100)",
            name=op.f("ck_grid_scores_total_range"),
        ),
        sa.ForeignKeyConstraint(
            ["cell_id"],
            ["grid_cells.id"],
            name=op.f("fk_grid_scores_cell_id_grid_cells"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["config_id"],
            ["score_configs.id"],
            name=op.f("fk_grid_scores_config_id_score_configs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grid_scores")),
        sa.UniqueConstraint(
            "cell_id",
            "config_id",
            "data_version",
            name=op.f("uq_grid_scores_cell_id_config_id_data_version"),
        ),
    )
    op.create_index(
        "ix_grid_scores_config_id_data_version",
        "grid_scores",
        ["config_id", "data_version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_grid_scores_config_id_data_version", table_name="grid_scores")
    op.drop_table("grid_scores")
    op.drop_index("ix_trade_area_metrics_lookup", table_name="trade_area_metrics")
    op.drop_table("trade_area_metrics")
    op.drop_index(op.f("ix_grid_cells_trade_area_id"), table_name="grid_cells")
    op.drop_geospatial_index(
        "ix_grid_cells_geom_gist",
        table_name="grid_cells",
        postgresql_using="gist",
        column_name="geom",
    )
    op.drop_index(op.f("ix_grid_cells_district_code"), table_name="grid_cells")
    op.drop_geospatial_table("grid_cells")
    op.drop_geospatial_index(
        "ix_trade_areas_geom_gist",
        table_name="trade_areas",
        postgresql_using="gist",
        column_name="geom",
    )
    op.drop_index(op.f("ix_trade_areas_district_code"), table_name="trade_areas")
    op.drop_geospatial_table("trade_areas")
    op.drop_table("score_configs")
    op.drop_table("score_baselines")
    op.drop_index(op.f("ix_saved_locations_owner_key"), table_name="saved_locations")
    op.drop_geospatial_index(
        "ix_saved_locations_geom_gist",
        table_name="saved_locations",
        postgresql_using="gist",
        column_name="geom",
    )
    op.drop_geospatial_table("saved_locations")
    op.drop_index("ix_pois_kind", table_name="pois")
    op.drop_geospatial_index(
        "ix_pois_geom_gist", table_name="pois", postgresql_using="gist", column_name="geom"
    )
    op.drop_geospatial_table("pois")
    op.drop_index(op.f("ix_etl_runs_pipeline"), table_name="etl_runs")
    op.drop_table("etl_runs")
    op.drop_index(op.f("ix_category_map_category_key"), table_name="category_map")
    op.drop_table("category_map")
    op.drop_geospatial_index(
        "ix_businesses_geom_gist",
        table_name="businesses",
        postgresql_using="gist",
        column_name="geom",
    )
    op.drop_index("ix_businesses_category_key_dataset_id", table_name="businesses")
    op.drop_geospatial_table("businesses")
    op.drop_index(op.f("ix_response_cache_expires_at"), table_name="response_cache")
    op.drop_index(op.f("ix_response_cache_data_version"), table_name="response_cache")
    op.drop_table("response_cache")
    op.drop_index(op.f("ix_datasets_key"), table_name="datasets")
    op.drop_table("datasets")
    op.drop_table("categories")
