"""
Authentication endpoints tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.database import get_session, init_db
from app.models import User
from app.auth import get_password_hash

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Setup test database for each test."""
    init_db()
    yield
    # Cleanup can be added here if needed


def get_test_session():
    """Get test database session."""
    return next(get_session())


class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_register_user_success(self):
        """Test successful user registration."""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123"  # Shorter password for bcrypt
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "created_at" in data
    
    def test_register_user_invalid_email(self):
        """Test registration with invalid email."""
        user_data = {
            "name": "Test User",
            "email": "invalid-email",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
    
    def test_register_user_short_password(self):
        """Test registration with short password."""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create first user
        user_data = {
            "name": "Test User 1",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        client.post("/auth/register", json=user_data)
        
        # Try to create second user with same email
        user_data2 = {
            "name": "Test User 2",
            "email": "test@example.com",
            "password": "testpass456"  # Shorter password
        }
        
        response = client.post("/auth/register", json=user_data2)
        assert response.status_code == 400
        
        data = response.json()
        assert "Email already registered" in data["detail"]
    
    def test_login_success(self):
        """Test successful login."""
        # Register user
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123"
        }
        client.post("/auth/register", json=user_data)
        
        # Login
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert "Incorrect email or password" in data["detail"]
    
    def test_get_current_user(self):
        """Test getting current user profile."""
        # Register and login
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"
    
    def test_get_current_user_unauthorized(self):
        """Test getting current user without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_refresh_token(self):
        """Test token refresh."""
        # Register and login
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        login_response = client.post("/auth/login", json=login_data)
        original_token = login_response.json()["access_token"]
        
        # Refresh token
        headers = {"Authorization": f"Bearer {original_token}"}
        response = client.post("/auth/refresh", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # New token should be different
        assert data["access_token"] != original_token


class TestInputValidation:
    """Test input validation across all endpoints."""
    
    def test_name_validation_xss(self):
        """Test XSS prevention in name fields."""
        malicious_names = [
            "<script>alert('xss')</script>",
            "Test <img src=x onerror=alert(1)> User",
            "Test\"&<>User",
            "javascript:alert('xss')"
        ]
        
        for malicious_name in malicious_names:
            user_data = {
                "name": malicious_name,
                "email": f"test{len(malicious_name)}@example.com",
                "password": "testpassword123"
            }
            
            response = client.post("/auth/register", json=user_data)
            assert response.status_code == 422
    
    def test_email_validation_formats(self):
        """Test various invalid email formats."""
        invalid_emails = [
            "plainaddress",
            "@missingdomain.com",
            "missing@.com",
            "spaces @example.com",
            "test@.com",
            "test@example.",
            "test@example..com"
        ]
        
        for invalid_email in invalid_emails:
            user_data = {
                "name": "Test User",
                "email": invalid_email,
                "password": "testpassword123"
            }
            
            response = client.post("/auth/register", json=user_data)
            assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
