from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.db import get_db
from app.api.v1.auth import get_current_user
from app.security.dependencies import require_role
from app.models.user import User, UserRole
from app.models.chat import ExpertRequest, ExpertRequestStatus
from app.schemas.expert import ExpertRequestCreate, ExpertRequestResponse, ExpertRequestResolve
from app.services.audit import write_audit_log
from app.security.rate_limit import RateLimiter

router = APIRouter(prefix="/expert", tags=["expert"])


@router.post("", response_model=ExpertRequestResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(10, 60))])
async def create_expert_request(
    request: ExpertRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an expert escalation request. Open to any authenticated user.
    """
    new_request = ExpertRequest(
        user_id=current_user.id,
        message_id=request.message_id,
        status=ExpertRequestStatus.OPEN,
        context=request.context,
    )
    db.add(new_request)

    await write_audit_log(
        db=db,
        user_id=current_user.id,
        action="EXPERT_REQUEST_CREATE",
        resource_type="ExpertRequest",
        resource_id=str(new_request.id),
        metadata_payload={"message_id": str(request.message_id) if request.message_id else None},
    )

    await db.commit()
    await db.refresh(new_request)
    return new_request


@router.get("", response_model=List[ExpertRequestResponse], dependencies=[Depends(RateLimiter(60, 60))])
async def list_expert_requests(
    status_filter: Optional[ExpertRequestStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.IP_FACILITATOR, UserRole.ADMIN)),
):
    """
    List expert requests. RBAC-gated to IP_FACILITATOR and ADMIN.
    """
    stmt = select(ExpertRequest).order_by(ExpertRequest.created_at.desc())
    if status_filter:
        stmt = stmt.where(ExpertRequest.status == status_filter)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.patch("/{request_id}", response_model=ExpertRequestResponse, dependencies=[Depends(RateLimiter(60, 60))])
async def resolve_expert_request(
    request_id: UUID,
    body: ExpertRequestResolve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.IP_FACILITATOR, UserRole.ADMIN)),
):
    """
    Update the status of an expert request. RBAC-gated to IP_FACILITATOR and ADMIN.
    """
    stmt = select(ExpertRequest).where(ExpertRequest.id == request_id)
    result = await db.execute(stmt)
    expert_req = result.scalar_one_or_none()

    if not expert_req:
        raise HTTPException(status_code=404, detail="Expert request not found")

    expert_req.status = body.status

    await write_audit_log(
        db=db,
        user_id=current_user.id,
        action="EXPERT_REQUEST_RESOLVE",
        resource_type="ExpertRequest",
        resource_id=str(request_id),
        metadata_payload={"new_status": body.status.value},
    )

    await db.commit()
    await db.refresh(expert_req)
    return expert_req
