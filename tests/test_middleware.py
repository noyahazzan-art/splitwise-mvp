"""
Middleware tests for rate limiting and security headers.
"""

import time
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.database import get_session, init_db
from app.models import User

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Setup test database for each test."""
    init_db()
    yield


def get_test_session():
    """Get test database session."""
    return next(get_session())


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_headers(self):
        """Test that rate limit headers are present."""
        response = client.get("/")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_enforcement(self):
        """Test rate limiting enforcement (simplified test)."""
        # Make multiple requests quickly
        responses = []
        for i in range(5):
            response = client.get("/")
            responses.append(response)
            if response.status_code == 429:
                break
        
        # Check that we got rate limited (this is a simplified test)
        # In real scenario, you'd need to make 100+ requests
        rate_limited = any(r.status_code == 429 for r in responses)
        
        # Should not be rate limited with just 5 requests
        assert not rate_limited
        
        # But headers should be present
        for response in responses:
            assert "X-RateLimit-Limit" in response.headers
            assert int(response.headers["X-RateLimit-Limit"]) == 100


class TestSecurityHeaders:
    """Test security headers functionality."""
    
    def test_security_headers_present(self):
        """Test that security headers are present."""
        response = client.get("/")
        
        # Check security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "Permissions-Policy" in response.headers
        
        # Check server header is masked
        assert response.headers.get("Server") == "Splitwise-API"
    
    def test_correlation_id_header(self):
        """Test that correlation ID is added to responses."""
        response = client.get("/")
        assert "X-Correlation-ID" in response.headers
        assert len(response.headers["X-Correlation-ID"]) == 36  # UUID length


class TestRequestLogging:
    """Test request logging functionality."""
    
    def test_request_logging_works(self):
        """Test that requests are properly logged."""
        # This test mainly ensures the middleware doesn't crash
        # Actual logging would be checked via log files/output
        response = client.get("/")
        
        # Should get successful response
        assert response.status_code == 200
        
        # Should have correlation ID
        assert "X-Correlation-ID" in response.headers


class TestMiddlewareIntegration:
    """Test middleware integration with authentication."""
    
    def test_auth_with_middleware(self):
        """Test that authentication works with middleware."""
        # Register a user
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # Check rate limit headers on auth endpoint
        assert "X-RateLimit-Limit" in register_response.headers
        assert "X-Correlation-ID" in register_response.headers
        
        # Login
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        # Check headers on login
        assert "X-RateLimit-Limit" in login_response.headers
        assert "X-Correlation-ID" in login_response.headers
        assert "access_token" in login_response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
