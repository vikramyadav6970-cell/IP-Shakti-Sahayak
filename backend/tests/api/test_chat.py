import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from app.models.user import User, UserRole
from datetime import datetime, timezone

dummy_user = User(
    id=uuid.uuid4(),
    email="test@example.com",
    name="Test User",
    hashed_password="hashed_pw",
    role=UserRole.USER,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc)
)

@pytest.mark.asyncio
async def test_chat_success(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "question": "What is the patent term?",
        "domain_intent": "PATENT",
        "jurisdiction": "India",
        "language": "en"
    }
    
    mock_conv = MagicMock()
    mock_conv.id = uuid.uuid4()
    
    with patch("app.security.dependencies.UserRepository.get_by_id", new_callable=AsyncMock) as mock_get_user, \
         patch("app.repositories.chat_repo.ChatRepository.create_conversation", new_callable=AsyncMock) as mock_create_conv, \
         patch("app.repositories.chat_repo.ChatRepository.add_message", new_callable=AsyncMock), \
         patch("app.repositories.chat_repo.ChatRepository.add_citation", new_callable=AsyncMock), \
         patch("app.services.audit.write_audit_log", new_callable=AsyncMock):
        mock_get_user.return_value = dummy_user
        mock_create_conv.return_value = mock_conv
        
        response = await client.post("/api/v1/chat", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "confidence" in data
        assert "requires_human_review" in data
        assert "conversation_id" in data

@pytest.mark.asyncio
async def test_chat_unauthorized(client: AsyncClient):
    payload = {
        "question": "Hello",
        "domain_intent": "OTHER",
        "jurisdiction": "India",
        "language": "en"
    }
    response = await client.post("/api/v1/chat", json=payload)
    assert response.status_code == 401
