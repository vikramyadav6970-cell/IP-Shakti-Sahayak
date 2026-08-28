from pydantic import BaseModel, Field
from typing import Optional, Any
from uuid import UUID
from datetime import datetime

from app.models.chat import ExpertRequestStatus


class ExpertRequestCreate(BaseModel):
    message_id: Optional[UUID] = None
    context: str = Field(..., min_length=1, max_length=2000)


class ExpertRequestResponse(BaseModel):
    id: UUID
    user_id: UUID
    message_id: Optional[UUID] = None
    status: ExpertRequestStatus
    context: str
    created_at: datetime


class ExpertRequestResolve(BaseModel):
    status: ExpertRequestStatus
