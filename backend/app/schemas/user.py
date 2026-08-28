from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from app.models.user import UserRole

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    language: str | None = None
    organization: str | None = Field(None, max_length=255)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

class UserResponse(UserBase):
    id: UUID
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True
