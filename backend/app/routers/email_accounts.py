from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.email_account import EmailAccount
from app.models.user import User
from app.schemas.email_account import EmailAccountCreate, EmailAccountResponse
from app.services import email_account_service

router = APIRouter(prefix="/email-accounts", tags=["email-accounts"])


@router.get("", response_model=list[EmailAccountResponse])
async def list_email_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EmailAccount]:
    return await email_account_service.list_email_accounts(db, current_user.id)


@router.post("", response_model=EmailAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_email_account(
    payload: EmailAccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmailAccount:
    return await email_account_service.create_email_account(db, current_user.id, payload)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_email_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    account = await email_account_service.get_email_account(db, current_user.id, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta de e-mail não encontrada")
    await email_account_service.delete_email_account(db, account)
