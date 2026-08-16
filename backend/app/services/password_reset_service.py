from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.services.auth_service import hash_password


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def create_reset_token(db: AsyncSession, user: User) -> str:
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_token_expire_minutes)

    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=expires_at,
        )
    )
    await db.commit()
    return raw_token


async def get_valid_token(db: AsyncSession, raw_token: str) -> PasswordResetToken | None:
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == _hash_token(raw_token))
    )
    token = result.scalar_one_or_none()
    if token is None or token.used_at is not None:
        return None
    if token.expires_at < datetime.now(timezone.utc):
        return None
    return token


async def consume_token_and_set_password(db: AsyncSession, token: PasswordResetToken, new_password: str) -> None:
    user = await db.get(User, token.user_id)
    if user is None:
        return

    user.hashed_password = hash_password(new_password)
    token.used_at = datetime.now(timezone.utc)
    await db.commit()
