from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.product import Product, Classification
from app.schemas.classification import ClassificationRequest, ClassificationResponse
from app.services.classification_service import classify_product
from app.services.audit import write_audit_log
from app.security.rate_limit import RateLimiter

router = APIRouter(prefix="/classification", tags=["classification"])

@router.post("", response_model=ClassificationResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(20, 60))])
async def create_classification(
    request: ClassificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Classify a product using the deterministic rules engine.
    Persists the Classification record including rules_fired for auditability.
    """
    # Verify product exists
    stmt = select(Product).where(Product.id == request.product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Call the rules engine (stubbed — will be replaced by ai/ layer)
    classification_result = classify_product(
        product_type=request.product_type,
        derived_from_authoritative_text=request.derived_from_authoritative_text,
        formulation_novelty=request.formulation_novelty,
        biological_resources_used=request.biological_resources_used,
    )

    # Persist the classification
    new_classification = Classification(
        product_id=request.product_id,
        category=classification_result["category"],
        regulatory_pathway=classification_result["regulatory_pathway"],
        rules_fired=classification_result["rules_fired"],
    )
    db.add(new_classification)

    # Audit log — DPDP compliance
    await write_audit_log(
        db=db,
        user_id=current_user.id,
        action="CLASSIFICATION_CREATE",
        resource_type="Classification",
        resource_id=str(request.product_id),
        metadata_payload={"category": classification_result["category"], "pathway": classification_result["regulatory_pathway"]},
    )

    await db.commit()
    await db.refresh(new_classification)

    return new_classification
