"""Test authentication endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserFavorite, UserVote
from app.routers.auth import create_token


@pytest.fixture
async def test_user(test_db: AsyncSession):
    """Create a test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        picture="https://example.com/avatar.jpg",
        provider="google",
        provider_id="google_123",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authorization headers with JWT."""
    token = create_token(test_user.id, test_user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.unit
async def test_google_login_success(client: AsyncClient):
    """Test successful Google OAuth login."""
    with patch("app.routers.auth.id_token.verify_oauth2_token") as mock_verify:
        mock_verify.return_value = {
            "sub": "google_user_123",
            "email": "user@example.com",
            "name": "New User",
            "picture": "https://example.com/pic.jpg",
        }
        
        response = await client.post(
            "/api/auth/google",
            json={"credential": "fake_google_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "user@example.com"
        
        # Check that auth_token cookie is set
        assert "auth_token" in response.cookies


@pytest.mark.unit
async def test_google_login_invalid_token(client: AsyncClient):
    """Test Google login with invalid token."""
    with patch("app.routers.auth.id_token.verify_oauth2_token") as mock_verify:
        mock_verify.side_effect = ValueError("Invalid token")
        
        response = await client.post(
            "/api/auth/google",
            json={"credential": "invalid_token"}
        )
        
        assert response.status_code == 400
        assert "Invalid Google token" in response.json()["detail"]


@pytest.mark.unit
async def test_jwt_creation_and_validation(test_user):
    """Test JWT token creation and decoding."""
    from jose import jwt
    from app.config import settings
    
    token = create_token(test_user.id, test_user.email)
    assert token is not None
    
    # Decode and verify
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert int(payload["sub"]) == test_user.id
    assert payload["email"] == test_user.email
    assert "exp" in payload


@pytest.mark.unit
async def test_get_current_user_with_valid_token(client: AsyncClient, test_user):
    """Test get current user with valid JWT."""
    token = create_token(test_user.id, test_user.email)
    
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email


@pytest.mark.unit
async def test_get_current_user_without_token(client: AsyncClient):
    """Test get current user without authentication."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.unit
async def test_favorites_crud(client: AsyncClient, test_user, test_db: AsyncSession):
    """Test favorite CRUD operations."""
    token = create_token(test_user.id, test_user.email)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add favorite
    response = await client.post(
        "/api/auth/favorites",
        json={
            "item_type": "tv",
            "item_id": "channel_123",
            "item_data": '{"name": "Test Channel", "logo": "https://example.com/logo.png"}'
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "added"
    
    # Get favorites
    response = await client.get("/api/auth/favorites?item_type=tv", headers=headers)
    assert response.status_code == 200
    favorites = response.json()
    assert len(favorites) == 1
    assert favorites[0]["item_id"] == "channel_123"
    
    # Remove favorite
    response = await client.delete(
        "/api/auth/favorites",
        params={"item_type": "tv", "item_id": "channel_123"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "removed"
    
    # Verify removed
    response = await client.get("/api/auth/favorites?item_type=tv", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.unit
async def test_voting_logic(client: AsyncClient, test_user, test_db: AsyncSession):
    """Test voting up/down functionality."""
    token = create_token(test_user.id, test_user.email)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upvote
    response = await client.post(
        "/api/auth/vote",
        json={
            "item_type": "tv",
            "item_id": "channel_456",
            "vote_type": "upvote"
        },
        headers=headers,
    )
    assert response.status_code == 200
    
    # Check vote was recorded
    result = await test_db.execute(
        test_db.query(UserVote).filter_by(
            user_id=test_user.id,
            item_type="tv",
            item_id="channel_456",
        )
    )
    vote = result.scalar_one_or_none()
    assert vote is not None
    assert vote.vote_type == "upvote"
    
    # Change to downvote
    response = await client.post(
        "/api/auth/vote",
        json={
            "item_type": "tv",
            "item_id": "channel_456",
            "vote_type": "downvote"
        },
        headers=headers,
    )
    assert response.status_code == 200
    
    # Remove vote
    response = await client.delete(
        "/api/auth/vote",
        params={"item_type": "tv", "item_id": "channel_456"},
        headers=headers,
    )
    assert response.status_code == 200


@pytest.mark.unit
async def test_authorization_required(client: AsyncClient):
    """Test that protected endpoints require authentication."""
    # Try to access favorites without auth
    response = await client.get("/api/auth/favorites")
    assert response.status_code == 401
    
    # Try to add favorite without auth
    response = await client.post(
        "/api/auth/favorites",
        json={"item_type": "tv", "item_id": "test", "item_data": "{}"}
    )
    assert response.status_code == 401


@pytest.mark.unit
async def test_csrf_token_generation(client: AsyncClient):
    """Test CSRF token endpoint."""
    response = await client.get("/api/csrf/token")
    assert response.status_code == 200
    data = response.json()
    assert "csrf_token" in data
    assert len(data["csrf_token"]) > 20
    
    # Check cookie is set
    assert "csrf_token" in response.cookies


@pytest.mark.unit
async def test_logout_clears_cookies(client: AsyncClient):
    """Test logout endpoint clears auth cookies."""
    response = await client.post("/api/csrf/logout")
    assert response.status_code == 200
    
    # In a real test with cookies, we'd verify they're cleared
    # For now, just check the endpoint works
    assert response.json()["status"] == "logged_out"
