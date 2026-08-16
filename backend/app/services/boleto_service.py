from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boleto import Boleto, BoletoOrigem, BoletoStatus
from app.schemas.boleto import BoletoCreate, BoletoUpdate
from app.services.pdf_parser import BoletoData


async def get_by_linha_digitavel(db: AsyncSession, linha_digitavel: str) -> Boleto | None:
    result = await db.execute(select(Boleto).where(Boleto.linha_digitavel == linha_digitavel))
    return result.scalar_one_or_none()


async def list_boletos(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: BoletoStatus | None = None,
    vencimento_de: date | None = None,
    vencimento_ate: date | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Boleto], int]:
    query = select(Boleto).where(Boleto.user_id == user_id)

    if status is not None:
        query = query.where(Boleto.status == status)
    if vencimento_de is not None:
        query = query.where(Boleto.data_vencimento >= vencimento_de)
    if vencimento_ate is not None:
        query = query.where(Boleto.data_vencimento <= vencimento_ate)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Boleto.data_vencimento.asc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_boleto(db: AsyncSession, user_id: uuid.UUID, boleto_id: uuid.UUID) -> Boleto | None:
    result = await db.execute(
        select(Boleto).where(Boleto.id == boleto_id, Boleto.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_boleto(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: BoletoCreate,
    origem: BoletoOrigem = BoletoOrigem.MANUAL,
    arquivo_pdf_path: str | None = None,
) -> Boleto:
    boleto = Boleto(
        user_id=user_id,
        origem=origem,
        arquivo_pdf_path=arquivo_pdf_path,
        **data.model_dump(),
    )
    db.add(boleto)
    await db.commit()
    await db.refresh(boleto)
    return boleto


async def create_password_protected_boleto(
    db: AsyncSession,
    user_id: uuid.UUID,
    beneficiario: str,
    origem: BoletoOrigem,
    arquivo_pdf_path: str,
) -> Boleto:
    boleto = Boleto(
        user_id=user_id,
        beneficiario=beneficiario,
        origem=origem,
        arquivo_pdf_path=arquivo_pdf_path,
        precisa_senha=True,
    )
    db.add(boleto)
    await db.commit()
    await db.refresh(boleto)
    return boleto


async def unlock_boleto(db: AsyncSession, boleto: Boleto, data: BoletoData) -> Boleto:
    boleto.valor = data.valor
    boleto.data_vencimento = data.vencimento
    boleto.linha_digitavel = data.linha_digitavel
    if data.beneficiario:
        boleto.beneficiario = data.beneficiario
    boleto.precisa_senha = False

    await db.commit()
    await db.refresh(boleto)
    return boleto


async def update_boleto(db: AsyncSession, boleto: Boleto, data: BoletoUpdate) -> Boleto:
    updates = data.model_dump(exclude_unset=True)

    if updates.get("status") == BoletoStatus.PAGO and boleto.data_pagamento is None and "data_pagamento" not in updates:
        updates["data_pagamento"] = date.today()

    for field, value in updates.items():
        setattr(boleto, field, value)

    await db.commit()
    await db.refresh(boleto)
    return boleto


async def delete_boleto(db: AsyncSession, boleto: Boleto) -> None:
    await db.delete(boleto)
    await db.commit()
