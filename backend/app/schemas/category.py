from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(max_length=100)
    color: str = Field(default="#64748b", pattern=r"^#[0-9a-fA-F]{6}$")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
