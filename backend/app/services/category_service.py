from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

DEFAULT_CATEGORIES: list[tuple[str, str]] = [
    ("Moradia", "#2563eb"),
    ("Energia", "#f59e0b"),
    ("Internet", "#8b5cf6"),
    ("Água", "#0284c7"),
    ("Educação", "#10b981"),
    ("Saúde", "#ef4444"),
    ("Outros", "#64748b"),
]


async def list_categories(db: AsyncSession, user_id: uuid.UUID) -> list[Category]:
    result = await db.execute(select(Category).where(Category.user_id == user_id).order_by(Category.name.asc()))
    return list(result.scalars().all())


async def get_category(db: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID) -> Category | None:
    result = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_category(db: AsyncSession, user_id: uuid.UUID, data: CategoryCreate) -> Category:
    category = Category(user_id=user_id, **data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def update_category(db: AsyncSession, category: Category, data: CategoryUpdate) -> Category:
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)
    return category


async def delete_category(db: AsyncSession, category: Category) -> None:
    await db.delete(category)
    await db.commit()


async def create_default_categories(db: AsyncSession, user_id: uuid.UUID) -> None:
    for name, color in DEFAULT_CATEGORIES:
        db.add(Category(user_id=user_id, name=name, color=color))
    await db.commit()


async def suggest_category(db: AsyncSession, user_id: uuid.UUID, beneficiario: str) -> Category | None:
    categories = await list_categories(db, user_id)
    beneficiario_lower = beneficiario.lower()

    best: Category | None = None
    for category in categories:
        if category.name.lower() in beneficiario_lower:
            if best is None or len(category.name) > len(best.name):
                best = category

    return best
