"""
Security and performance middleware for Splitwise MVP.
"""

import time
import uuid
from collections import defaultdict, deque
from typing import Dict, Optional

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with in-memory storage."""
    
    def __init__(self, app: FastAPI, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # Number of allowed calls
        self.period = period  # Time period in seconds
        self.clients: Dict[str, deque] = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with rate limiting."""
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Clean old requests
        current_time = time.time()
        self._cleanup_old_requests(client_id, current_time)
        
        # Check rate limit
        if len(self.clients[client_id]) >= self.calls:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "Retry-After": str(self.period),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + self.period))
                }
            )
        
        # Add current request
        self.clients[client_id].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.calls - len(self.clients[client_id])
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from IP or user ID."""
        # Try to get user ID from request state (set by auth middleware)
        if hasattr(request.state, 'user') and request.state.user:
            return f"user:{request.state.user.id}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return f"ip:{real_ip}"
        
        return f"ip:{request.client.host}"
    
    def _cleanup_old_requests(self, client_id: str, current_time: float):
        """Remove requests older than the time period."""
        cutoff_time = current_time - self.period
        while self.clients[client_id] and self.clients[client_id][0] < cutoff_time:
            self.clients[client_id].popleft()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request and add security headers."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Remove server information
        response.headers["Server"] = "Splitwise-API"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced request logging with correlation IDs."""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with enhanced logging."""
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        # Log request start
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Log request completion
        self._log_request(request, response, duration, correlation_id)
        
        return response
    
    def _log_request(self, request: Request, response: Response, duration: float, correlation_id: str):
        """Log request details."""
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get user info if available
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = request.state.user.id
        
        # Log structured information
        log_data = {
            "correlation_id": correlation_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "user_id": user_id,
            "user_agent": request.headers.get("User-Agent", ""),
            "ip": self._get_client_ip(request)
        }
        
        # Log based on status code
        if response.status_code >= 500:
            logger.error(f"Request failed: {log_data}")
        elif response.status_code >= 400:
            logger.warning(f"Request error: {log_data}")
        else:
            logger.info(f"Request completed: {log_data}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


def setup_middleware(app: FastAPI) -> None:
    """Setup all middleware for the application."""
    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add rate limiting (100 calls per minute)
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)
    
    # Add request logging
    app.add_middleware(RequestLoggingMiddleware)
