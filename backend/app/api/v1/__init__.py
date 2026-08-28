from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.documents import router as documents_router
from app.api.v1.context import router as context_router
from app.api.v1.chat import router as chat_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.classification import router as classification_router
from app.api.v1.ip import router as ip_router
from app.api.v1.abs import router as abs_router
from app.api.v1.expert import router as expert_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(documents_router)
api_router.include_router(context_router)
api_router.include_router(chat_router)
api_router.include_router(feedback_router)
api_router.include_router(classification_router)
api_router.include_router(ip_router)
api_router.include_router(abs_router)
api_router.include_router(expert_router)
