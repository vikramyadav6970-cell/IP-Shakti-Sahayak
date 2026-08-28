from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import BaseModel
import uuid
from typing import Any

class Product(BaseModel):
    __tablename__ = "products"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_ingredients: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)

class Classification(BaseModel):
    __tablename__ = "classifications"
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    category: Mapped[str] = mapped_column(String(100))
    regulatory_pathway: Mapped[str] = mapped_column(String(255))
    rules_fired: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSONB)

class IPAssessment(BaseModel):
    __tablename__ = "ip_assessments"
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    ip_type: Mapped[str] = mapped_column(String(50), index=True)
    relevance_label: Mapped[str] = mapped_column(String(50))
    reasoning: Mapped[str] = mapped_column(Text)
    legal_provisions: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSONB)

class ABSAssessment(BaseModel):
    __tablename__ = "abs_assessments"
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    biological_resources: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSONB)
    origin: Mapped[str | None] = mapped_column(String(100), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(100), nullable=True)
    relevance_label: Mapped[str] = mapped_column(String(50))
    next_steps: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSONB)
