"""Seed categories and the initial cafe score configuration.

Source-code mappings (category_map) are added in Step 2, after the SEMAS and golmok
classification codes have been verified against the dataset pages.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

categories = sa.table("categories", sa.column("key"), sa.column("name_ko"), sa.column("enabled"))
score_configs = sa.table(
    "score_configs",
    sa.column("category_key"),
    sa.column("version"),
    sa.column("weights", JSONB),
    sa.column("min_coverage"),
    sa.column("definition", JSONB),
    sa.column("is_active"),
    sa.column("note"),
)


def upgrade() -> None:
    op.bulk_insert(
        categories,
        [
            {"key": "cafe", "name_ko": "카페", "enabled": True},
            {"key": "restaurant", "name_ko": "음식점", "enabled": False},
            {"key": "convenience_store", "name_ko": "편의점", "enabled": False},
        ],
    )
    op.bulk_insert(
        score_configs,
        [
            {
                "category_key": "cafe",
                "version": "v1",
                "weights": {
                    "demand": 0.35,
                    "competition": 0.25,
                    "accessibility": 0.20,
                    "growth": 0.10,
                    "cost": 0.10,
                },
                "min_coverage": 0.70,
                "definition": {},  # component metric definitions are filled in Step 5
                "is_active": True,
                "note": "초기 가정값(검증되지 않음). 사용자가 조정 가능.",
            }
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM score_configs WHERE category_key = 'cafe' AND version = 'v1'")
    op.execute("DELETE FROM categories WHERE key IN ('cafe', 'restaurant', 'convenience_store')")
