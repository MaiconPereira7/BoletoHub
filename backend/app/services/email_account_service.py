from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_account import EmailAccount
from app.schemas.email_account import EmailAccountCreate
from app.services.crypto import encrypt


async def list_email_accounts(db: AsyncSession, user_id: uuid.UUID) -> list[EmailAccount]:
    result = await db.execute(
        select(EmailAccount).where(EmailAccount.user_id == user_id).order_by(EmailAccount.created_at.asc())
    )
    return list(result.scalars().all())


async def get_email_account(db: AsyncSession, user_id: uuid.UUID, account_id: uuid.UUID) -> EmailAccount | None:
    result = await db.execute(
        select(EmailAccount).where(EmailAccount.id == account_id, EmailAccount.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_email_account(db: AsyncSession, user_id: uuid.UUID, data: EmailAccountCreate) -> EmailAccount:
    account = EmailAccount(
        user_id=user_id,
        email=data.email,
        imap_host=data.imap_host,
        imap_port=data.imap_port,
        imap_password_encrypted=encrypt(data.imap_password),
        imap_use_ssl=data.imap_use_ssl,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def delete_email_account(db: AsyncSession, account: EmailAccount) -> None:
    await db.delete(account)
    await db.commit()
