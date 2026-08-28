from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.security.auth import get_password_hash
from typing import Optional
from uuid import UUID

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, user_create: UserCreate) -> User:
        db_user = User(
            name=user_create.name,
            email=user_create.email,
            language=user_create.language,
            organization=user_create.organization,
            hashed_password=get_password_hash(user_create.password)
        )
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user
