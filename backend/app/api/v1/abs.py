from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.product import Product, ABSAssessment
from app.schemas.assessment import ABSAssessmentRequest, ABSAssessmentResponse
from app.services.assessment_service import assess_abs_obligations
from app.services.audit import write_audit_log
from app.security.rate_limit import RateLimiter

router = APIRouter(prefix="/abs", tags=["abs"])

@router.post("", response_model=ABSAssessmentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(20, 60))])
async def create_abs_assessment(
    request: ABSAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assess ABS (Access and Benefit Sharing) obligations for a product.
    Persists the result to ABSAssessment.
    """
    # Verify product exists
    stmt = select(Product).where(Product.id == request.product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Call the AI layer stub
    assessment = assess_abs_obligations(
        product_id=str(request.product_id),
        biological_resources=request.biological_resources,
        origin=request.origin,
        purpose=request.purpose,
    )

    # Persist
    new_assessment = ABSAssessment(
        product_id=request.product_id,
        biological_resources=request.biological_resources,
        origin=request.origin,
        purpose=request.purpose,
        relevance_label=assessment["relevance_label"],
        next_steps=assessment["next_steps"],
    )
    db.add(new_assessment)

    await write_audit_log(
        db=db,
        user_id=current_user.id,
        action="ABS_ASSESSMENT_CREATE",
        resource_type="ABSAssessment",
        resource_id=str(request.product_id),
        metadata_payload={"relevance": assessment["relevance_label"], "resource_count": len(request.biological_resources)},
    )

    await db.commit()
    await db.refresh(new_assessment)

    return new_assessment
