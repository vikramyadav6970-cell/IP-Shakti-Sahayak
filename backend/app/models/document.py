from sqlalchemy import String, ForeignKey, Enum, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
import enum
import uuid
from datetime import datetime

class DocumentType(str, enum.Enum):
    STATUTE = "STATUTE"
    RULE = "RULE"
    TREATY = "TREATY"
    REGISTRY_RECORD = "REGISTRY_RECORD"
    CASE_LAW = "CASE_LAW"
    GUIDELINE = "GUIDELINE"
    FORM = "FORM"

class IngestionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"

class Document(BaseModel):
    __tablename__ = "documents"
    title: Mapped[str] = mapped_column(String(255))
    jurisdiction: Mapped[str] = mapped_column(String(50), index=True)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), index=True)
    authority: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    corpus_collection: Mapped[str] = mapped_column(String(100), index=True)

class DocumentVersion(BaseModel):
    __tablename__ = "document_versions"
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    version_label: Mapped[str] = mapped_column(String(50))
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    storage_key: Mapped[str] = mapped_column(String)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    ingestion_status: Mapped[IngestionStatus] = mapped_column(Enum(IngestionStatus), default=IngestionStatus.PENDING, index=True)
