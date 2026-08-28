from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.chat import Feedback, Message
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.security.rate_limit import RateLimiter
from typing import List

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(20, 60))])
async def submit_feedback(
    request: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit feedback for a specific message.
    """
    # Verify message exists
    stmt = select(Message).where(Message.id == request.message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    new_feedback = Feedback(
        message_id=request.message_id,
        user_id=current_user.id,
        rating=request.rating,
        comment=request.comment
    )
    
    db.add(new_feedback)
    await db.commit()
    await db.refresh(new_feedback)
    
    return new_feedback
