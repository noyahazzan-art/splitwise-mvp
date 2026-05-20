"""
Authentication module for Splitwise MVP.
JWT-based authentication with secure password hashing.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

import bcrypt
from jose import JWTError, jwt  # type: ignore[import-untyped]
import re

from pydantic import BaseModel, Field, field_validator

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set. Set it before starting the server.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30



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
    password: str = Field(..., min_length=8)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if re.search(r"[<>\"'&]", v):
            raise ValueError("Name contains invalid characters")
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Reject double dots and ensure each domain label is valid
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$"
        cleaned = v.strip()
        if not re.match(pattern, cleaned) or ".." in cleaned:
            raise ValueError("Invalid email format")
        return cleaned.lower()


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
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
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
