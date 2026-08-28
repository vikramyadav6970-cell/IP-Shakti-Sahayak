import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_chat_success(client: AsyncClient, access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "question": "What is the patent term?",
        "domain_intent": "PATENT",
        "jurisdiction": "India",
        "language": "en"
    }
    
    response = await client.post("/api/v1/chat", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["confidence"] > 0
    assert data["requires_human_review"] is False
    assert len(data["citations"]) > 0
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
