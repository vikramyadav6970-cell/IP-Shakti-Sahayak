from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.db import get_db
from app.models.user import User, UserRole
from app.models.document import DocumentType
from app.schemas.document import DocumentResponse, DocumentCreate, DocumentUpdate, DocumentVersionResponse
from app.security.dependencies import get_current_user, require_role
from app.repositories.document_repo import DocumentRepository
from app.security.rate_limit import RateLimiter

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("", response_model=List[DocumentResponse], dependencies=[Depends(RateLimiter(60, 60))])
async def list_documents(
    jurisdiction: Optional[str] = Query(None),
    document_type: Optional[DocumentType] = Query(None),
    corpus_collection: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Text search across document titles"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents with optional filtering and text search. Open to all authenticated users."""
    repo = DocumentRepository(db)
    docs = await repo.list_documents(
        skip=skip, 
        limit=limit, 
        jurisdiction=jurisdiction, 
        document_type=document_type, 
        corpus_collection=corpus_collection,
        search=search
    )
    return docs

@router.get("/{document_id}", response_model=DocumentResponse, dependencies=[Depends(RateLimiter(60, 60))])
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document by ID."""
    repo = DocumentRepository(db)
    doc = await repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(60, 60))])
async def create_document(
    doc_create: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.CONTENT_MANAGER))
):
    """Create a new document metadata record (Admin/Content Manager only)."""
    repo = DocumentRepository(db)
    return await repo.create(doc_create)

@router.patch("/{document_id}", response_model=DocumentResponse, dependencies=[Depends(RateLimiter(60, 60))])
async def update_document(
    document_id: UUID,
    doc_update: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.CONTENT_MANAGER))
):
    """Update document metadata (Admin/Content Manager only)."""
    repo = DocumentRepository(db)
    doc = await repo.update(document_id, doc_update)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RateLimiter(60, 60))])
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.CONTENT_MANAGER))
):
    """Delete a document (Admin/Content Manager only)."""
    repo = DocumentRepository(db)
    success = await repo.delete(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return None

@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse], dependencies=[Depends(RateLimiter(60, 60))])
async def list_document_versions(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all versions for a specific document."""
    repo = DocumentRepository(db)
    doc = await repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    versions = await repo.list_versions(document_id)
    return versions

from fastapi import UploadFile, File, Form
from app.services.storage import storage_service
import uuid

@router.post("/{document_id}/versions", response_model=DocumentVersionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(20, 60))])
async def create_document_version(
    document_id: UUID,
    version_label: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.CONTENT_MANAGER))
):
    """Upload a new version for a document (Admin/Content Manager only)."""
    repo = DocumentRepository(db)
    doc = await repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Upload to Supabase Storage
    # Create a unique key like documents/{doc_id}/{version_label}_{uuid}.pdf
    extension = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    object_name = f"documents/{document_id}/{version_label}_{uuid.uuid4().hex[:8]}.{extension}"
    
    try:
        storage_key = storage_service.upload(file.file, object_name, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")
        
    # Record in DB
    new_version = await repo.create_version(document_id, version_label, storage_key)
    return new_version

from app.workers.celery_app import celery_app
from app.models.document import IngestionStatus
from app.schemas.ingestion import IngestionStatusResponse

@router.post("/{version_id}/ingest", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(RateLimiter(20, 60))])
async def trigger_ingestion(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.CONTENT_MANAGER))
):
    """Trigger ingestion for a specific document version (Admin/Content Manager only)."""
    repo = DocumentRepository(db)
    version = await repo.get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found")
        
    # Enqueue task in Celery
    # Note: the task signature must match the AI worker's signature exactly
    celery_app.send_task("ai.tasks.ingest_document", args=[str(version_id)])
    
    # Update status to PROCESSING
    await repo.update_version_status(version_id, IngestionStatus.PROCESSING)
    return {"message": "Ingestion triggered successfully", "version_id": str(version_id)}

@router.get("/{version_id}/ingest/status", response_model=IngestionStatusResponse, dependencies=[Depends(RateLimiter(60, 60))])
async def get_ingestion_status(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check the ingestion status of a document version."""
    repo = DocumentRepository(db)
    version = await repo.get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found")
        
    return IngestionStatusResponse(
        version_id=str(version.id),
        status=version.ingestion_status
    )
