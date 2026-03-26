"""Pydantic schemas for API request/response with comprehensive validation."""

import re
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models import ExpenseCategory, MemberRole


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input by removing potentially dangerous characters."""
    if not value:
        return ""
    # Remove HTML tags and special characters
    cleaned = re.sub(r'<[^>]+>', '', value)
    cleaned = re.sub(r'["\'&<>]', '', cleaned)
    return cleaned.strip()[:max_length]


def validate_email_format(email: str) -> str:
    """Validate email format."""
    if not email:
        raise ValueError("Email is required")
    
    email = email.strip().lower()
    if len(email) > 255:
        raise ValueError("Email too long (max 255 characters)")
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    
    return email


# --- User ---
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="User full name")
    email: str = Field(..., description="User email address")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")
        
        # Check for dangerous characters
        if any(char in v for char in ['<', '>', '"', "'", '&', 'script']):
            raise ValueError("Name contains invalid characters")
        
        return sanitize_string(v, 255)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_format(v)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255, description="User full name")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is None:
            return v
        
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")
        
        # Check for dangerous characters
        if any(char in v for char in ['<', '>', '"', "'", '&', 'script']):
            raise ValueError("Name contains invalid characters")
        
        return sanitize_string(v, 255)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Group ---
class GroupCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Group name")
    
    @field_validator('name')
    @classmethod
    def validate_group_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Group name must be at least 2 characters long")
        
        # Check for dangerous characters
        if any(char in v for char in ['<', '>', '"', "'", '&', 'script']):
            raise ValueError("Group name contains invalid characters")
        
        return sanitize_string(v, 255)


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255, description="Group name")
    
    @field_validator('name')
    @classmethod
    def validate_group_name(cls, v):
        if v is None:
            return v
        
        if len(v.strip()) < 2:
            raise ValueError("Group name must be at least 2 characters long")
        
        # Check for dangerous characters
        if any(char in v for char in ['<', '>', '"', "'", '&', 'script']):
            raise ValueError("Group name contains invalid characters")
        
        return sanitize_string(v, 255)


class GroupAddMember(BaseModel):
    user_id: int = Field(..., gt=0, description="User ID to add to group")
    role: MemberRole = Field(MemberRole.MEMBER, description="Member role")


class GroupResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Expense ---
class ExpenseShareInput(BaseModel):
    user_id: int = Field(..., gt=0, description="User ID for share")
    share_amount: float = Field(..., gt=0, description="Share amount (must be positive)")


class ExpenseCreate(BaseModel):
    group_id: int = Field(..., gt=0, description="Group ID")
    payer_id: int = Field(..., gt=0, description="Payer user ID")
    amount: float = Field(..., gt=0, le=1000000, description="Expense amount (positive, max 1M)")
    currency: str = Field("ILS", min_length=3, max_length=3, description="Currency code (3 letters)")
    description: str = Field(..., min_length=1, max_length=500, description="Expense description")
    category: ExpenseCategory = Field(ExpenseCategory.OTHER, description="Expense category")
    # For equal split: omit shares, participants = all group members
    # For manual: provide shares (must sum to amount)
    shares: Optional[List[ExpenseShareInput]] = Field(None, description="Manual expense shares")
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if not v or len(v) != 3 or not v.isalpha():
            raise ValueError("Currency must be 3-letter code (e.g., USD, ILS)")
        return v.upper()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError("Description is required")
        
        # Check for dangerous characters
        if any(char in v for char in ['<', '>', '"', "'", '&', 'script']):
            raise ValueError("Description contains invalid characters")
        
        return sanitize_string(v, 500)
    
    @model_validator(mode='after')
    def validate_expense_shares(self):
        """Validate: if shares provided, sum must equal amount (within 0.01)."""
        if self.shares is not None and len(self.shares) > 0:
            total = sum(s.share_amount for s in self.shares)
            if abs(total - self.amount) > 0.01:
                raise ValueError(f"ExpenseShare sum ({total}) must equal amount ({self.amount})")
            
            # Check for duplicate user IDs
            user_ids = [s.user_id for s in self.shares]
            if len(user_ids) != len(set(user_ids)):
                raise ValueError("Duplicate user IDs in expense shares")
        
        return self


class ExpenseUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=1, max_length=500, description="Expense description")
    category: Optional[ExpenseCategory] = Field(None, description="Expense category")
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is None:
            return v
        
        if len(v.strip()) < 1:
            raise ValueError("Description is required")
        
        # Check for dangerous characters
        if any(char in v for char in ['<', '>', '"', "'", '&', 'script']):
            raise ValueError("Description contains invalid characters")
        
        return sanitize_string(v, 500)


class ExpenseResponse(BaseModel):
    id: int
    group_id: int
    payer_id: int
    amount: float
    currency: str
    description: str
    category: ExpenseCategory
    date: datetime

    model_config = {"from_attributes": True}


# --- Balance ---
class BalanceEntry(BaseModel):
    user_id: int = Field(..., gt=0, description="User ID")
    balance: float = Field(..., description="Balance amount (positive = owed to them, negative = they owe)")


class SettlementEntry(BaseModel):
    from_user_id: int = Field(..., gt=0, description="User who owes money")
    to_user_id: int = Field(..., gt=0, description="User who is owed money")
    amount: float = Field(..., gt=0, description="Settlement amount (must be positive)")
    
    @model_validator(mode='after')
    def validate_settlement(self):
        """Validate settlement users are different."""
        if self.from_user_id == self.to_user_id:
            raise ValueError("From user and to user must be different")
        return self


# --- API Response wrappers ---
class APIResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None
