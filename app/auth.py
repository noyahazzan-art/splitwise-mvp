"""
Authentication module for Splitwise MVP.
JWT-based authentication with secure password hashing.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model for parsing JWT payload."""
    user_id: Optional[int] = None
    email: Optional[str] = None


class UserCreate(BaseModel):
    """User registration model."""
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    """User login model."""
    email: str
    password: str


class UserResponse(BaseModel):
    """User response model (without password)."""
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify JWT token and extract user data."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        if user_id is None or email is None:
            return None
        token_data = TokenData(user_id=user_id, email=email)
        return token_data
    except JWTError:
        return None


def authenticate_user(user_email: str, user_password: str, user_hashed_password: str) -> bool:
    """Authenticate user credentials."""
    return verify_password(user_password, user_hashed_password)
