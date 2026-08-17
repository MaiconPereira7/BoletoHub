from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserResponse,
)
from app.services import category_service, password_reset_service
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_user_by_email,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])

GENERIC_FORGOT_PASSWORD_MESSAGE = "Se esse e-mail existir na nossa base, enviamos um link de redefinição de senha."


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    existing = await get_user_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já cadastrado")

    user = await register_user(db, payload.email, payload.password, payload.full_name)
    await category_service.create_default_categories(db, user.id)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict:
    user = await get_user_by_email(db, payload.email)
    if user is not None and user.is_active:
        raw_token = await password_reset_service.create_reset_token(db, user)
        reset_url = f"{settings.frontend_url}/redefinir-senha?token={raw_token}"
        celery_app.send_task(
            "app.tasks.send_password_reset_email_task",
            kwargs={"to": user.email, "reset_url": reset_url},
        )

    return {"message": GENERIC_FORGOT_PASSWORD_MESSAGE}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict:
    token = await password_reset_service.get_valid_token(db, payload.token)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Link de redefinição inválido ou expirado"
        )

    await password_reset_service.consume_token_and_set_password(db, token, payload.new_password)
    return {"message": "Senha redefinida com sucesso"}
