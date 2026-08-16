from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import date

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.config import settings
from app.database import async_session_factory, engine
from app.models.boleto import Boleto, BoletoOrigem, BoletoStatus
from app.models.email_account import EmailAccount
from app.models.scan_log import ScanLog, ScanLogStatus
from app.models.user import User
from app.schemas.boleto import BoletoCreate
from app.services import boleto_service
from app.services.crypto import decrypt
from app.services.email_service import MailboxConfig, fetch_boleto_candidates, legacy_mailbox
from app.services.mailer import render_password_reset_email, send_email
from app.services.pdf_parser import PdfPasswordProtectedError, parse_boleto_pdf

logger = logging.getLogger(__name__)


async def _run_isolated(coro):
    """Executa a coroutine e libera o pool de conexões antes do loop do asyncio.run() fechar.

    Cada chamada de task Celery roda em um novo loop via asyncio.run(); sem descartar o pool
    aqui, a próxima task reaproveitaria conexões presas ao loop anterior (já encerrado).
    """
    try:
        return await coro
    finally:
        await engine.dispose()


async def _mailboxes_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[MailboxConfig]:
    boxes: list[MailboxConfig] = []

    legacy = legacy_mailbox()
    if legacy:
        boxes.append(legacy)

    result = await db.execute(
        select(EmailAccount).where(EmailAccount.user_id == user_id, EmailAccount.ativo.is_(True))
    )
    for account in result.scalars():
        boxes.append(
            MailboxConfig(
                host=account.imap_host,
                port=account.imap_port,
                username=account.email,
                password=decrypt(account.imap_password_encrypted),
                use_ssl=account.imap_use_ssl,
            )
        )

    return boxes


async def _resolve_periodic_user_ids(db: AsyncSession) -> list[uuid.UUID]:
    result = await db.execute(select(EmailAccount.user_id).distinct())
    user_ids = [row[0] for row in result.all()]
    if user_ids:
        return user_ids

    result = await db.execute(
        select(User).where(User.is_superuser.is_(True)).order_by(User.created_at.asc()).limit(1)
    )
    user = result.scalar_one_or_none()
    return [user.id] if user else []


async def _run_scan_for_user(user_id: uuid.UUID) -> dict:
    async with async_session_factory() as db:
        mailboxes = await _mailboxes_for_user(db, user_id)

    if not mailboxes:
        return {"boletos_found": 0, "error": "Nenhuma caixa de e-mail configurada"}

    candidates = []
    mailbox_errors: list[str] = []
    for mailbox in mailboxes:
        try:
            candidates.extend(fetch_boleto_candidates(mailbox))
        except Exception as exc:  # noqa: BLE001 - uma caixa fora do ar não pode impedir as demais
            logger.exception("Falha ao conectar ao IMAP (%s)", mailbox.username)
            mailbox_errors.append(f"{mailbox.username}: {exc}")

    boletos_found = 0

    async with async_session_factory() as db:
        for candidate in candidates:
            already_seen = await db.execute(
                select(ScanLog.id).where(ScanLog.email_message_id == candidate.message_id).limit(1)
            )
            if already_seen.scalar_one_or_none() is not None:
                continue

            try:
                data = parse_boleto_pdf(candidate.content)
            except PdfPasswordProtectedError:
                user_dir = os.path.join(settings.boleto_storage_dir, str(user_id))
                os.makedirs(user_dir, exist_ok=True)
                file_path = os.path.join(user_dir, f"{uuid.uuid4()}.pdf")
                with open(file_path, "wb") as fh:
                    fh.write(candidate.content)

                boleto = await boleto_service.create_password_protected_boleto(
                    db,
                    user_id,
                    beneficiario=candidate.subject or "PDF protegido por senha",
                    origem=BoletoOrigem.EMAIL,
                    arquivo_pdf_path=file_path,
                )

                db.add(
                    ScanLog(
                        user_id=user_id,
                        boleto_id=boleto.id,
                        email_message_id=candidate.message_id,
                        email_subject=candidate.subject,
                        email_from=candidate.from_,
                        status=ScanLogStatus.SUCESSO,
                        mensagem="Boleto protegido por senha adicionado — informe a senha para ver os dados",
                    )
                )
                await db.commit()
                boletos_found += 1
                continue
            except Exception as exc:  # noqa: BLE001 - um PDF corrompido não pode derrubar o scan inteiro
                logger.exception("Falha ao processar PDF do e-mail %s", candidate.message_id)
                db.add(
                    ScanLog(
                        user_id=user_id,
                        email_message_id=candidate.message_id,
                        email_subject=candidate.subject,
                        email_from=candidate.from_,
                        status=ScanLogStatus.ERRO,
                        mensagem=f"Erro ao processar PDF: {exc}",
                    )
                )
                await db.commit()
                continue

            if data is None:
                db.add(
                    ScanLog(
                        user_id=user_id,
                        email_message_id=candidate.message_id,
                        email_subject=candidate.subject,
                        email_from=candidate.from_,
                        status=ScanLogStatus.IGNORADO,
                        mensagem="Não foi possível extrair dados de boleto do PDF anexado",
                    )
                )
                await db.commit()
                continue

            existing = None
            if data.linha_digitavel:
                existing = await boleto_service.get_by_linha_digitavel(db, data.linha_digitavel)

            if existing is not None:
                db.add(
                    ScanLog(
                        user_id=user_id,
                        boleto_id=existing.id,
                        email_message_id=candidate.message_id,
                        email_subject=candidate.subject,
                        email_from=candidate.from_,
                        status=ScanLogStatus.IGNORADO,
                        mensagem="Boleto já cadastrado (linha digitável duplicada)",
                    )
                )
                await db.commit()
                continue

            user_dir = os.path.join(settings.boleto_storage_dir, str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            file_path = os.path.join(user_dir, f"{uuid.uuid4()}.pdf")
            with open(file_path, "wb") as fh:
                fh.write(candidate.content)

            payload = BoletoCreate(
                beneficiario=data.beneficiario or "Não identificado",
                valor=data.valor,
                data_vencimento=data.vencimento,
                linha_digitavel=data.linha_digitavel,
            )
            boleto = await boleto_service.create_boleto(
                db, user_id, payload, origem=BoletoOrigem.EMAIL, arquivo_pdf_path=file_path
            )

            db.add(
                ScanLog(
                    user_id=user_id,
                    boleto_id=boleto.id,
                    email_message_id=candidate.message_id,
                    email_subject=candidate.subject,
                    email_from=candidate.from_,
                    status=ScanLogStatus.SUCESSO,
                    mensagem="Boleto criado a partir de e-mail",
                )
            )
            await db.commit()
            boletos_found += 1

    return {"boletos_found": boletos_found, "error": "; ".join(mailbox_errors) if mailbox_errors else None}


async def _run_scan(user_id: str | None) -> dict:
    async with async_session_factory() as db:
        if user_id:
            user_ids = [uuid.UUID(user_id)]
        else:
            user_ids = await _resolve_periodic_user_ids(db)

    if not user_ids:
        return {"boletos_found": 0, "error": "Nenhum usuário disponível para receber os boletos escaneados"}

    total_found = 0
    errors: list[str] = []
    for uid in user_ids:
        result = await _run_scan_for_user(uid)
        total_found += result.get("boletos_found", 0)
        if result.get("error"):
            errors.append(result["error"])

    return {"boletos_found": total_found, "error": "; ".join(errors) if errors else None}


@celery_app.task(name="app.tasks.scan_emails_task")
def scan_emails_task(user_id: str | None = None) -> dict:
    """Varre as caixas de e-mail configuradas em busca de novos boletos."""
    return asyncio.run(_run_isolated(_run_scan(user_id)))


async def _update_overdue_boletos() -> int:
    async with async_session_factory() as db:
        result = await db.execute(
            update(Boleto)
            .where(Boleto.status == BoletoStatus.PENDENTE, Boleto.data_vencimento < date.today())
            .values(status=BoletoStatus.VENCIDO)
        )
        await db.commit()
        return result.rowcount or 0


@celery_app.task(name="app.tasks.update_overdue_boletos_task")
def update_overdue_boletos_task() -> dict:
    """Atualiza boletos pendentes com vencimento no passado para 'vencido'."""
    updated = asyncio.run(_run_isolated(_update_overdue_boletos()))
    return {"updated": updated}


@celery_app.task(name="app.tasks.send_password_reset_email_task")
def send_password_reset_email_task(to: str, reset_url: str) -> dict:
    """Envia o e-mail de redefinição de senha (via SMTP)."""
    try:
        send_email(to, "Redefinir senha — BoletoHub", render_password_reset_email(reset_url))
    except Exception as exc:  # noqa: BLE001 - falha de envio não deve derrubar o worker
        logger.exception("Falha ao enviar e-mail de redefinição de senha para %s", to)
        return {"sent": False, "error": str(exc)}
    return {"sent": True}
