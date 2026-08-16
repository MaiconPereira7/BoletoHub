"""initial schema: users, boletos, scan_logs

Revision ID: 0001
Revises:
Create Date: 2026-08-02

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

boleto_status = postgresql.ENUM("pendente", "pago", "vencido", name="boleto_status", create_type=False)
boleto_origem = postgresql.ENUM("email", "manual", name="boleto_origem", create_type=False)
scan_log_status = postgresql.ENUM("sucesso", "erro", "ignorado", name="scan_log_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    boleto_status.create(bind, checkfirst=True)
    boleto_origem.create(bind, checkfirst=True)
    scan_log_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "boletos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("beneficiario", sa.String(length=255), nullable=False),
        sa.Column("pagador", sa.String(length=255), nullable=True),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("linha_digitavel", sa.String(length=64), nullable=True),
        sa.Column("codigo_barras", sa.String(length=64), nullable=True),
        sa.Column("data_vencimento", sa.Date(), nullable=False),
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        sa.Column("status", boleto_status, nullable=False, server_default="pendente"),
        sa.Column("origem", boleto_origem, nullable=False, server_default="manual"),
        sa.Column("arquivo_pdf_path", sa.String(length=500), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_boletos_user_id", "boletos", ["user_id"])
    op.create_index("ix_boletos_status", "boletos", ["status"])
    op.create_unique_constraint("uq_boletos_linha_digitavel", "boletos", ["linha_digitavel"])

    op.create_table(
        "scan_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "boleto_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("boletos.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("email_message_id", sa.String(length=255), nullable=True),
        sa.Column("email_subject", sa.String(length=500), nullable=True),
        sa.Column("email_from", sa.String(length=255), nullable=True),
        sa.Column("status", scan_log_status, nullable=False, server_default="sucesso"),
        sa.Column("mensagem", sa.Text(), nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scan_logs_user_id", "scan_logs", ["user_id"])
    op.create_index("ix_scan_logs_boleto_id", "scan_logs", ["boleto_id"])
    op.create_index("ix_scan_logs_status", "scan_logs", ["status"])


def downgrade() -> None:
    op.drop_table("scan_logs")
    op.drop_table("boletos")
    op.drop_table("users")

    scan_log_status.drop(op.get_bind(), checkfirst=True)
    boleto_origem.drop(op.get_bind(), checkfirst=True)
    boleto_status.drop(op.get_bind(), checkfirst=True)
