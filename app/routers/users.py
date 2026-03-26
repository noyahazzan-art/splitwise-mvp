"""User API with authentication."""

import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth import UserResponse
from app.database import get_session
from app.dependencies import get_current_active_user, get_optional_current_user
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


def validate_email(email: str) -> bool:
    """Validate email format and basic security."""
    if not email or len(email) > 255:
        return False
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_name(name: str) -> bool:
    """Validate user name for basic security."""
    if not name or len(name.strip()) < 2 or len(name) > 255:
        return False
    # Prevent basic injection attempts
    if any(char in name for char in ['<', '>', '"', "'", '&', 'script']):
        return False
    return True


@router.get("/", response_model=List[UserResponse])
def list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all users (authenticated only)."""
    users = session.exec(select(User)).all()
    return list(users)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile."""
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID (authenticated only)."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update user name (authenticated users can only update themselves)."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own profile"
        )
    
    if not validate_name(name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid name format"
        )
    
    current_user.name = name.strip()[:255]
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user
