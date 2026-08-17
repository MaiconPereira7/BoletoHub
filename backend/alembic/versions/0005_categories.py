"""categories: categorização de boletos

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-16

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False, server_default="#64748b"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    op.add_column(
        "boletos",
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_boletos_category_id", "boletos", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_boletos_category_id", table_name="boletos")
    op.drop_column("boletos", "category_id")
    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_table("categories")
