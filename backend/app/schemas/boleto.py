from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.boleto import BoletoOrigem, BoletoStatus


class BoletoBase(BaseModel):
    beneficiario: str = Field(max_length=255)
    pagador: str | None = Field(default=None, max_length=255)
    valor: Decimal = Field(gt=0, decimal_places=2)
    linha_digitavel: str | None = Field(default=None, max_length=64)
    codigo_barras: str | None = Field(default=None, max_length=64)
    data_vencimento: date
    observacoes: str | None = None


class BoletoCreate(BoletoBase):
    pass


class BoletoUpdate(BaseModel):
    beneficiario: str | None = Field(default=None, max_length=255)
    pagador: str | None = Field(default=None, max_length=255)
    valor: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    linha_digitavel: str | None = Field(default=None, max_length=64)
    codigo_barras: str | None = Field(default=None, max_length=64)
    data_vencimento: date | None = None
    data_pagamento: date | None = None
    status: BoletoStatus | None = None
    observacoes: str | None = None


class BoletoResponse(BoletoBase):
    model_config = ConfigDict(from_attributes=True)

    valor: Decimal | None = Field(default=None, decimal_places=2)
    data_vencimento: date | None = None

    id: uuid.UUID
    user_id: uuid.UUID
    status: BoletoStatus
    origem: BoletoOrigem
    precisa_senha: bool
    data_pagamento: date | None
    arquivo_pdf_path: str | None
    created_at: datetime
    updated_at: datetime


class BoletoListResponse(BaseModel):
    items: list[BoletoResponse]
    total: int
    page: int
    limit: int


class BoletoUnlockRequest(BaseModel):
    senha: str = Field(min_length=1)
