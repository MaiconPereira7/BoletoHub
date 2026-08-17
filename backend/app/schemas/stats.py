from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from app.schemas.boleto import BoletoResponse


class MesGastoItem(BaseModel):
    mes: str
    total_pago: Decimal


class CategoriaGastoItem(BaseModel):
    categoria: str
    valor: Decimal


class BoletoStatsResponse(BaseModel):
    total_pendente: Decimal
    total_pago: Decimal
    total_vencido: Decimal
    contagem_por_status: dict[str, int]
    gastos_por_mes: list[MesGastoItem]
    gastos_por_categoria: list[CategoriaGastoItem]
    proximos_vencer: list[BoletoResponse]
