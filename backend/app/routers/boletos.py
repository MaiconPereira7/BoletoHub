from __future__ import annotations

import os
import uuid
from datetime import date

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.boleto import Boleto, BoletoOrigem, BoletoStatus
from app.models.user import User
from app.schemas.boleto import BoletoCreate, BoletoListResponse, BoletoResponse, BoletoUnlockRequest, BoletoUpdate
from app.schemas.scan import ScanStatusResponse, ScanTriggerResponse
from app.services import boleto_service
from app.services.pdf_parser import PdfPasswordProtectedError, parse_boleto_pdf

router = APIRouter(prefix="/boletos", tags=["boletos"])


async def _get_owned_boleto(db: AsyncSession, current_user: User, boleto_id: uuid.UUID) -> Boleto:
    boleto = await boleto_service.get_boleto(db, current_user.id, boleto_id)
    if boleto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boleto não encontrado")
    return boleto


@router.get("", response_model=BoletoListResponse)
async def list_boletos(
    status_filter: BoletoStatus | None = Query(default=None, alias="status"),
    vencimento_de: date | None = None,
    vencimento_ate: date | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BoletoListResponse:
    items, total = await boleto_service.list_boletos(
        db, current_user.id, status_filter, vencimento_de, vencimento_ate, page, limit
    )
    return BoletoListResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=BoletoResponse, status_code=status.HTTP_201_CREATED)
async def create_boleto(
    payload: BoletoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Boleto:
    if payload.linha_digitavel:
        existing = await boleto_service.get_by_linha_digitavel(db, payload.linha_digitavel)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Já existe um boleto com essa linha digitável"
            )

    return await boleto_service.create_boleto(db, current_user.id, payload, origem=BoletoOrigem.MANUAL)


@router.post("/upload", response_model=BoletoResponse, status_code=status.HTTP_201_CREATED)
async def upload_boleto_pdf(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Boleto:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O arquivo deve ser um PDF")

    pdf_bytes = await file.read()
    try:
        data = parse_boleto_pdf(pdf_bytes)
    except PdfPasswordProtectedError:
        data = None
        password_protected = True
    else:
        password_protected = False

    if not password_protected and data is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Não foi possível extrair os dados do boleto a partir do PDF",
        )

    if data and data.linha_digitavel:
        existing = await boleto_service.get_by_linha_digitavel(db, data.linha_digitavel)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Já existe um boleto com essa linha digitável"
            )

    user_dir = os.path.join(settings.boleto_storage_dir, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, f"{uuid.uuid4()}.pdf")
    with open(file_path, "wb") as fh:
        fh.write(pdf_bytes)

    if password_protected:
        return await boleto_service.create_password_protected_boleto(
            db,
            current_user.id,
            beneficiario=file.filename or "PDF protegido por senha",
            origem=BoletoOrigem.MANUAL,
            arquivo_pdf_path=file_path,
        )

    payload = BoletoCreate(
        beneficiario=data.beneficiario or "Não identificado",
        valor=data.valor,
        data_vencimento=data.vencimento,
        linha_digitavel=data.linha_digitavel,
    )
    return await boleto_service.create_boleto(
        db, current_user.id, payload, origem=BoletoOrigem.MANUAL, arquivo_pdf_path=file_path
    )


@router.post("/{boleto_id}/desbloquear", response_model=BoletoResponse)
async def unlock_boleto(
    boleto_id: uuid.UUID,
    payload: BoletoUnlockRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Boleto:
    boleto = await _get_owned_boleto(db, current_user, boleto_id)

    if not boleto.precisa_senha or not boleto.arquivo_pdf_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Este boleto não está protegido por senha"
        )

    try:
        with open(boleto.arquivo_pdf_path, "rb") as fh:
            pdf_bytes = fh.read()
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Arquivo do boleto não encontrado"
        ) from exc

    try:
        data = parse_boleto_pdf(pdf_bytes, password=payload.senha)
    except PdfPasswordProtectedError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Senha incorreta") from exc

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Senha correta, mas não foi possível extrair os dados do boleto a partir do PDF",
        )

    if data.linha_digitavel:
        existing = await boleto_service.get_by_linha_digitavel(db, data.linha_digitavel)
        if existing is not None and existing.id != boleto.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Já existe um boleto com essa linha digitável"
            )

    return await boleto_service.unlock_boleto(db, boleto, data)


@router.get("/scan/{task_id}", response_model=ScanStatusResponse)
async def get_scan_status(task_id: str, current_user: User = Depends(get_current_user)) -> ScanStatusResponse:
    result = AsyncResult(task_id, app=celery_app)

    if result.state == "PENDING":
        return ScanStatusResponse(task_id=task_id, state="pending")
    if result.state == "FAILURE":
        return ScanStatusResponse(task_id=task_id, state="failed", error=str(result.result))
    if result.state == "SUCCESS":
        info = result.result or {}
        error = info.get("error")
        return ScanStatusResponse(
            task_id=task_id,
            state="failed" if error else "completed",
            boletos_found=info.get("boletos_found"),
            error=error,
        )

    return ScanStatusResponse(task_id=task_id, state=result.state.lower())


@router.post("/scan", response_model=ScanTriggerResponse)
async def trigger_scan(current_user: User = Depends(get_current_user)) -> ScanTriggerResponse:
    async_result = celery_app.send_task("app.tasks.scan_emails_task", kwargs={"user_id": str(current_user.id)})
    return ScanTriggerResponse(task_id=async_result.id)


@router.get("/{boleto_id}", response_model=BoletoResponse)
async def get_boleto(
    boleto_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Boleto:
    return await _get_owned_boleto(db, current_user, boleto_id)


@router.patch("/{boleto_id}", response_model=BoletoResponse)
async def update_boleto(
    boleto_id: uuid.UUID,
    payload: BoletoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Boleto:
    boleto = await _get_owned_boleto(db, current_user, boleto_id)
    return await boleto_service.update_boleto(db, boleto, payload)


@router.delete("/{boleto_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_boleto(
    boleto_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    boleto = await _get_owned_boleto(db, current_user, boleto_id)
    await boleto_service.delete_boleto(db, boleto)
