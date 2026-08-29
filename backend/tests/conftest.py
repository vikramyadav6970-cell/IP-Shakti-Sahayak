import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db import get_db
from app.models.user import User, UserRole
from app.security.auth import create_access_token, get_password_hash

test_user_id = uuid.uuid4()
dummy_hashed_pw = get_password_hash("secret123")
dummy_user = User(
    id=test_user_id,
    email="test@example.com",
    name="Test User",
    hashed_password=dummy_hashed_pw,
    role=UserRole.USER,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc)
)

async def override_get_db():
    mock_session = AsyncMock()
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def access_token():
    return create_access_token(subject=str(test_user_id))

import pytest_asyncio

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
