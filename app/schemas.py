"""Pydantic schemas for API request/response."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models import ExpenseCategory, MemberRole


# --- User ---
class UserCreate(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime


# --- Group ---
class GroupCreate(BaseModel):
    name: str
    owner_id: int


class GroupAddMember(BaseModel):
    user_id: int
    role: MemberRole = MemberRole.MEMBER


class GroupResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime


# --- Expense ---
class ExpenseShareInput(BaseModel):
    user_id: int
    share_amount: float


class ExpenseCreate(BaseModel):
    group_id: int
    payer_id: int
    amount: float
    currency: str = "ILS"
    description: str
    category: ExpenseCategory = ExpenseCategory.OTHER
    # For equal split: omit shares, participants = all group members
    # For manual: provide shares (must sum to amount)
    shares: Optional[list[ExpenseShareInput]] = None

    def model_post_init(self, __context) -> None:
        """Validate: if shares provided, sum must equal amount (within 0.01)."""
        if self.shares is not None and len(self.shares) > 0:
            total = sum(s.share_amount for s in self.shares)
            if abs(total - self.amount) > 0.01:
                raise ValueError(f"ExpenseShare sum ({total}) must equal amount ({self.amount})")


class ExpenseResponse(BaseModel):
    id: int
    group_id: int
    payer_id: int
    amount: float
    currency: str
    description: str
    category: ExpenseCategory
    date: datetime


# --- Balance ---
class BalanceEntry(BaseModel):
    user_id: int
    balance: float  # positive = owed to them, negative = they owe


class SettlementEntry(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: float
