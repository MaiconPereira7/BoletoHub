from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.boleto import Boleto, BoletoOrigem, BoletoStatus
from app.models.category import Category
from app.schemas.boleto import BoletoCreate, BoletoUpdate
from app.schemas.stats import BoletoStatsResponse, CategoriaGastoItem, MesGastoItem
from app.services.pdf_parser import BoletoData


async def get_by_linha_digitavel(db: AsyncSession, linha_digitavel: str) -> Boleto | None:
    result = await db.execute(select(Boleto).where(Boleto.linha_digitavel == linha_digitavel))
    return result.scalar_one_or_none()


async def _reload_with_category(db: AsyncSession, boleto_id: uuid.UUID) -> Boleto:
    result = await db.execute(
        select(Boleto)
        .where(Boleto.id == boleto_id)
        .options(selectinload(Boleto.category))
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()


async def list_boletos(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: BoletoStatus | None = None,
    vencimento_de: date | None = None,
    vencimento_ate: date | None = None,
    category_id: uuid.UUID | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Boleto], int]:
    query = select(Boleto).where(Boleto.user_id == user_id).options(selectinload(Boleto.category))

    if status is not None:
        query = query.where(Boleto.status == status)
    if vencimento_de is not None:
        query = query.where(Boleto.data_vencimento >= vencimento_de)
    if vencimento_ate is not None:
        query = query.where(Boleto.data_vencimento <= vencimento_ate)
    if category_id is not None:
        query = query.where(Boleto.category_id == category_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Boleto.data_vencimento.asc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_boleto(db: AsyncSession, user_id: uuid.UUID, boleto_id: uuid.UUID) -> Boleto | None:
    result = await db.execute(
        select(Boleto)
        .where(Boleto.id == boleto_id, Boleto.user_id == user_id)
        .options(selectinload(Boleto.category))
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
    return await _reload_with_category(db, boleto.id)


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
    return await _reload_with_category(db, boleto.id)


async def unlock_boleto(db: AsyncSession, boleto: Boleto, data: BoletoData) -> Boleto:
    boleto.valor = data.valor
    boleto.data_vencimento = data.vencimento
    boleto.linha_digitavel = data.linha_digitavel
    if data.beneficiario:
        boleto.beneficiario = data.beneficiario
    boleto.precisa_senha = False

    await db.commit()
    return await _reload_with_category(db, boleto.id)


async def update_boleto(db: AsyncSession, boleto: Boleto, data: BoletoUpdate) -> Boleto:
    updates = data.model_dump(exclude_unset=True)

    if updates.get("status") == BoletoStatus.PAGO and boleto.data_pagamento is None and "data_pagamento" not in updates:
        updates["data_pagamento"] = date.today()

    for field, value in updates.items():
        setattr(boleto, field, value)

    await db.commit()
    return await _reload_with_category(db, boleto.id)


async def delete_boleto(db: AsyncSession, boleto: Boleto) -> None:
    await db.delete(boleto)
    await db.commit()


def _month_range(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end


def _last_n_months(today: date, n: int) -> list[tuple[date, date, str]]:
    months: list[tuple[date, date, str]] = []
    for offset in range(n - 1, -1, -1):
        total_month_index = today.year * 12 + (today.month - 1) - offset
        year, month = divmod(total_month_index, 12)
        month += 1
        start, end = _month_range(year, month)
        months.append((start, end, f"{year:04d}-{month:02d}"))
    return months


async def get_stats(db: AsyncSession, user_id: uuid.UUID) -> BoletoStatsResponse:
    today = date.today()
    month_start, next_month_start = _month_range(today.year, today.month)

    total_pendente = await db.scalar(
        select(func.coalesce(func.sum(Boleto.valor), 0)).where(
            Boleto.user_id == user_id,
            Boleto.status == BoletoStatus.PENDENTE,
            Boleto.data_vencimento >= month_start,
            Boleto.data_vencimento < next_month_start,
        )
    )
    total_vencido = await db.scalar(
        select(func.coalesce(func.sum(Boleto.valor), 0)).where(
            Boleto.user_id == user_id,
            Boleto.status == BoletoStatus.VENCIDO,
            Boleto.data_vencimento >= month_start,
            Boleto.data_vencimento < next_month_start,
        )
    )
    total_pago = await db.scalar(
        select(func.coalesce(func.sum(Boleto.valor), 0)).where(
            Boleto.user_id == user_id,
            Boleto.status == BoletoStatus.PAGO,
            Boleto.data_pagamento >= month_start,
            Boleto.data_pagamento < next_month_start,
        )
    )

    contagem_result = await db.execute(
        select(Boleto.status, func.count()).where(Boleto.user_id == user_id).group_by(Boleto.status)
    )
    contagem_por_status = {status.value: count for status, count in contagem_result.all()}

    gastos_por_mes: list[MesGastoItem] = []
    for start, end, label in _last_n_months(today, 6):
        total = await db.scalar(
            select(func.coalesce(func.sum(Boleto.valor), 0)).where(
                Boleto.user_id == user_id,
                Boleto.status == BoletoStatus.PAGO,
                Boleto.data_pagamento >= start,
                Boleto.data_pagamento < end,
            )
        )
        gastos_por_mes.append(MesGastoItem(mes=label, total_pago=total))

    gastos_categoria_result = await db.execute(
        select(Category.name, func.sum(Boleto.valor))
        .select_from(Boleto)
        .outerjoin(Category, Boleto.category_id == Category.id)
        .where(
            Boleto.user_id == user_id,
            Boleto.status == BoletoStatus.PAGO,
            Boleto.data_pagamento >= month_start,
            Boleto.data_pagamento < next_month_start,
        )
        .group_by(Category.name)
    )
    gastos_por_categoria = [
        CategoriaGastoItem(categoria=nome or "Sem categoria", valor=valor)
        for nome, valor in gastos_categoria_result.all()
    ]

    proximos_result = await db.execute(
        select(Boleto)
        .where(Boleto.user_id == user_id, Boleto.status == BoletoStatus.PENDENTE)
        .options(selectinload(Boleto.category))
        .order_by(Boleto.data_vencimento.asc())
        .limit(5)
    )
    proximos_vencer = list(proximos_result.scalars().all())

    return BoletoStatsResponse(
        total_pendente=total_pendente,
        total_pago=total_pago,
        total_vencido=total_vencido,
        contagem_por_status=contagem_por_status,
        gastos_por_mes=gastos_por_mes,
        gastos_por_categoria=gastos_por_categoria,
        proximos_vencer=proximos_vencer,
    )
