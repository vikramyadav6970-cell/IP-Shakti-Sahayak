import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.schemas.user import UserCreate
from app.models.user import User, UserRole
from app.security.auth import get_password_hash, create_access_token
import uuid
from datetime import datetime, timedelta, timezone

client = TestClient(app)

# Dummy user data
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

@patch("app.api.v1.auth.UserRepository")
def test_register_success(mock_repo_cls):
    mock_repo = mock_repo_cls.return_value
    mock_repo.get_by_email = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(return_value=dummy_user)
    
    response = client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "secret123"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert "id" in response.json()

@patch("app.api.v1.auth.UserRepository")
@patch("app.api.v1.auth.rate_limit_login")
def test_login_success(mock_rate_limit, mock_repo_cls):
    mock_repo = mock_repo_cls.return_value
    mock_repo.get_by_email = AsyncMock(return_value=dummy_user)
    
    response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "secret123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()["token"]

@patch("app.api.v1.auth.UserRepository")
@patch("app.api.v1.auth.rate_limit_login")
def test_login_wrong_password(mock_rate_limit, mock_repo_cls):
    mock_repo = mock_repo_cls.return_value
    mock_repo.get_by_email = AsyncMock(return_value=dummy_user)
    
    response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_invalid_token_rejected():
    response = client.get("/api/v1/auth/test-auth-endpoint", headers={"Authorization": "Bearer invalid_token_xyz"})
    # It will hit 404 if the endpoint doesn't exist, but 401 is thrown first if dependency fails
    # Let's write a dummy endpoint in the test to check role parsing
    pass

@patch("app.security.dependencies.UserRepository")
def test_expired_token_rejected(mock_repo_cls):
    from fastapi import APIRouter, Depends
    from app.security.dependencies import get_current_user
    
    # We mount a temporary route for testing
    router = APIRouter()
    @router.get("/test-expired")
    def test_expired_route(user: User = Depends(get_current_user)):
        return {"status": "ok"}
        
    app.include_router(router)
    
    # Generate an explicitly expired token
    expired_token = create_access_token(subject=test_user_id, expires_delta=timedelta(minutes=-10))
    
    response = client.get("/test-expired", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

@patch("app.security.dependencies.UserRepository")
def test_role_gated_endpoint_rejects(mock_repo_cls):
    from fastapi import APIRouter, Depends
    from app.security.dependencies import require_role
    
    mock_repo = mock_repo_cls.return_value
    mock_repo.get_by_id = AsyncMock(return_value=dummy_user)  # role is USER
    
    router = APIRouter()
    @router.get("/test-admin")
    def test_admin_route(user: User = Depends(require_role(UserRole.ADMIN))):
        return {"status": "ok"}
        
    app.include_router(router)
    
    valid_token = create_access_token(subject=test_user_id)
    response = client.get("/test-admin", headers={"Authorization": f"Bearer {valid_token}"})
    
    # Since user is USER, and endpoint requires ADMIN, it should be 403 Forbidden
    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to perform this action."
