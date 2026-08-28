from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.document import Document, DocumentVersion, DocumentType
from app.schemas.document import DocumentCreate, DocumentUpdate
from typing import Optional, List
from uuid import UUID

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        stmt = select(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_documents(
        self, 
        skip: int = 0, 
        limit: int = 100,
        jurisdiction: Optional[str] = None,
        document_type: Optional[DocumentType] = None,
        corpus_collection: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Document]:
        stmt = select(Document).order_by(Document.created_at.desc())
        
        if jurisdiction:
            stmt = stmt.where(Document.jurisdiction == jurisdiction)
        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        if corpus_collection:
            stmt = stmt.where(Document.corpus_collection == corpus_collection)
        if search:
            stmt = stmt.where(Document.title.ilike(f"%{search}%"))
            
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, doc_create: DocumentCreate) -> Document:
        db_doc = Document(**doc_create.model_dump())
        self.session.add(db_doc)
        await self.session.commit()
        await self.session.refresh(db_doc)
        return db_doc
        
    async def update(self, document_id: UUID, doc_update: DocumentUpdate) -> Optional[Document]:
        db_doc = await self.get_by_id(document_id)
        if not db_doc:
            return None
            
        update_data = doc_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_doc, key, value)
            
        await self.session.commit()
        await self.session.refresh(db_doc)
        return db_doc
        
    async def delete(self, document_id: UUID) -> bool:
        stmt = delete(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def list_versions(self, document_id: UUID) -> List[DocumentVersion]:
        stmt = select(DocumentVersion).where(DocumentVersion.document_id == document_id).order_by(DocumentVersion.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_version(self, document_id: UUID, version_label: str, storage_key: str) -> DocumentVersion:
        # Mark all previous versions as not current
        stmt = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id, 
            DocumentVersion.is_current == True
        )
        result = await self.session.execute(stmt)
        current_versions = result.scalars().all()
        for version in current_versions:
            version.is_current = False
            
        new_version = DocumentVersion(
            document_id=document_id,
            version_label=version_label,
            storage_key=storage_key,
            is_current=True
        )
        self.session.add(new_version)
        await self.session.commit()
        await self.session.refresh(new_version)
        return new_version

    async def get_version(self, version_id: UUID) -> Optional[DocumentVersion]:
        stmt = select(DocumentVersion).where(DocumentVersion.id == version_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_version_status(self, version_id: UUID, status: IngestionStatus) -> Optional[DocumentVersion]:
        version = await self.get_version(version_id)
        if not version:
            return None
            
        version.ingestion_status = status
        await self.session.commit()
        await self.session.refresh(version)
        return version
