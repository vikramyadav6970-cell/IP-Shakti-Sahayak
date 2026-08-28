from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import BaseModel
import uuid
from typing import Any

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    # Append-only — no update/delete path for this table, ever.
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    metadata_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True) # Renamed from 'metadata' to avoid conflict with SQLAlchemy Base
