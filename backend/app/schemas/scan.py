from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.scan_log import ScanLogStatus


class ScanTriggerResponse(BaseModel):
    task_id: str


class ScanStatusResponse(BaseModel):
    task_id: str
    state: str
    boletos_found: int | None = None
    error: str | None = None


class ScanLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    boleto_id: uuid.UUID | None
    email_message_id: str | None
    email_subject: str | None
    email_from: str | None
    status: ScanLogStatus
    mensagem: str | None
    scanned_at: datetime
