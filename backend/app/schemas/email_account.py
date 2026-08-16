from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmailAccountCreate(BaseModel):
    email: EmailStr
    imap_host: str = Field(default="imap.gmail.com", max_length=255)
    imap_port: int = Field(default=993, gt=0, le=65535)
    imap_password: str = Field(min_length=1)
    imap_use_ssl: bool = True


class EmailAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    imap_host: str
    imap_port: int
    imap_use_ssl: bool
    ativo: bool
    created_at: datetime
