from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class FeedbackCreate(BaseModel):
    message_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)

class FeedbackResponse(BaseModel):
    id: UUID
    message_id: UUID
    user_id: UUID
    rating: int
    comment: Optional[str] = None
