from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel
import enum

class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    IP_FACILITATOR = "IP_FACILITATOR"
    CONTENT_MANAGER = "CONTENT_MANAGER"
    RESEARCHER = "RESEARCHER"

class User(BaseModel):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, index=True)
