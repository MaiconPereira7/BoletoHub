from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


async def _get_owned_category(db: AsyncSession, current_user: User, category_id: uuid.UUID) -> Category:
    category = await category_service.get_category(db, current_user.id, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    return category


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Category]:
    return await category_service.list_categories(db, current_user.id)


@router.get("/suggest", response_model=CategoryResponse | None)
async def suggest_category(
    beneficiario: str = Query(min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Category | None:
    return await category_service.suggest_category(db, current_user.id, beneficiario)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Category:
    return await category_service.create_category(db, current_user.id, payload)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Category:
    category = await _get_owned_category(db, current_user, category_id)
    return await category_service.update_category(db, category, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    category = await _get_owned_category(db, current_user, category_id)
    await category_service.delete_category(db, category)
