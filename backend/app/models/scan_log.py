from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.boleto import Boleto


class ScanLogStatus(str, enum.Enum):
    SUCESSO = "sucesso"
    ERRO = "erro"
    IGNORADO = "ignorado"


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    boleto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("boletos.id", ondelete="SET NULL"), nullable=True, index=True
    )

    email_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email_from: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[ScanLogStatus] = mapped_column(
        SAEnum(ScanLogStatus, name="scan_log_status", native_enum=True, values_callable=lambda enum: [e.value for e in enum]),
        default=ScanLogStatus.SUCESSO,
        nullable=False,
        index=True,
    )
    mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)

    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    boleto: Mapped["Boleto | None"] = relationship(back_populates="scan_logs")

    def __repr__(self) -> str:
        return f"<ScanLog id={self.id} status={self.status}>"
