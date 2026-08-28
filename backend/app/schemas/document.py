from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.document import DocumentType, IngestionStatus

class DocumentBase(BaseModel):
    title: str
    jurisdiction: str
    document_type: DocumentType
    authority: Optional[str] = None
    language: str = "en"
    source_url: Optional[str] = None
    corpus_collection: str

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    jurisdiction: Optional[str] = None
    document_type: Optional[DocumentType] = None
    authority: Optional[str] = None
    language: Optional[str] = None
    source_url: Optional[str] = None
    corpus_collection: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_label: str
    effective_from: Optional[datetime]
    storage_key: str
    is_current: bool
    ingestion_status: IngestionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
