from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.security.dependencies import get_current_user, require_role
from app.repositories.user_repo import UserRepository
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get the profile of the currently authenticated user."""
    return current_user

@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """(Admin only) List all users in the system with pagination."""
    repo = UserRepository(db)
    users = await repo.list_users(skip=skip, limit=limit)
    return users
