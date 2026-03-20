"""User API."""

import re
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import User
from app.schemas import UserCreate, UserResponse

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


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    """Register a new user. Email must be unique."""
    # Input validation
    if not validate_email(user.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if not validate_name(user.name):
        raise HTTPException(status_code=400, detail="Invalid name format")
    
    existing = session.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Sanitize input
    clean_name = user.name.strip()[:255]
    clean_email = user.email.strip().lower()
    
    db_user = User(name=clean_name, email=clean_email)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get("/", response_model=list[UserResponse])
def list_users(session: Session = Depends(get_session)):
    """List all users."""
    users = session.exec(select(User)).all()
    return list(users)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, session: Session = Depends(get_session)):
    """Get user by ID."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
