from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.scan_log import ScanLog
    from app.models.user import User


class BoletoStatus(str, enum.Enum):
    PENDENTE = "pendente"
    PAGO = "pago"
    VENCIDO = "vencido"


class BoletoOrigem(str, enum.Enum):
    EMAIL = "email"
    MANUAL = "manual"


class Boleto(Base):
    __tablename__ = "boletos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    beneficiario: Mapped[str] = mapped_column(String(255), nullable=False)
    pagador: Mapped[str | None] = mapped_column(String(255), nullable=True)
    valor: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    linha_digitavel: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    codigo_barras: Mapped[str | None] = mapped_column(String(64), nullable=True)

    data_vencimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_pagamento: Mapped[date | None] = mapped_column(Date, nullable=True)

    precisa_senha: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[BoletoStatus] = mapped_column(
        SAEnum(BoletoStatus, name="boleto_status", native_enum=True, values_callable=lambda enum: [e.value for e in enum]),
        default=BoletoStatus.PENDENTE,
        nullable=False,
        index=True,
    )
    origem: Mapped[BoletoOrigem] = mapped_column(
        SAEnum(BoletoOrigem, name="boleto_origem", native_enum=True, values_callable=lambda enum: [e.value for e in enum]),
        default=BoletoOrigem.MANUAL,
        nullable=False,
    )

    arquivo_pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="boletos")
    category: Mapped["Category | None"] = relationship()
    scan_logs: Mapped[list["ScanLog"]] = relationship(
        back_populates="boleto", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Boleto id={self.id} beneficiario={self.beneficiario} status={self.status}>"
