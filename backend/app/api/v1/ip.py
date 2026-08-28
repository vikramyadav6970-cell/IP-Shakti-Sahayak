from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.product import Product, IPAssessment
from app.schemas.assessment import IPAssessmentRequest, IPAssessmentResponse
from app.services.assessment_service import assess_ip_relevance
from app.services.audit import write_audit_log
from app.security.rate_limit import RateLimiter

router = APIRouter(prefix="/ip", tags=["ip"])

@router.post("", response_model=IPAssessmentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(20, 60))])
async def create_ip_assessment(
    request: IPAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assess IP-type relevance for a classified product.
    Persists the result to IPAssessment.
    """
    # Verify product exists
    stmt = select(Product).where(Product.id == request.product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Call the AI layer stub
    assessment = assess_ip_relevance(
        product_id=str(request.product_id),
        ip_type=request.ip_type,
    )

    # Persist
    new_assessment = IPAssessment(
        product_id=request.product_id,
        ip_type=assessment["ip_type"],
        relevance_label=assessment["relevance_label"],
        reasoning=assessment["reasoning"],
        legal_provisions=assessment["legal_provisions"],
    )
    db.add(new_assessment)

    await write_audit_log(
        db=db,
        user_id=current_user.id,
        action="IP_ASSESSMENT_CREATE",
        resource_type="IPAssessment",
        resource_id=str(request.product_id),
        metadata_payload={"ip_type": request.ip_type, "relevance": assessment["relevance_label"]},
    )

    await db.commit()
    await db.refresh(new_assessment)

    return new_assessment
