"""boletos: suporte a PDF protegido por senha

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "boletos",
        sa.Column("precisa_senha", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("boletos", "valor", existing_type=sa.Numeric(12, 2), nullable=True)
    op.alter_column("boletos", "data_vencimento", existing_type=sa.Date(), nullable=True)


def downgrade() -> None:
    op.alter_column("boletos", "data_vencimento", existing_type=sa.Date(), nullable=False)
    op.alter_column("boletos", "valor", existing_type=sa.Numeric(12, 2), nullable=False)
    op.drop_column("boletos", "precisa_senha")
