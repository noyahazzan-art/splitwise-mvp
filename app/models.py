"""
Splitwise MVP — Database models (SQLModel).

Design: prevents duplicates, supports balance/settlement logic.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


# --- Enums ---
class MemberRole(str, Enum):
    OWNER = "owner"
    MEMBER = "member"


class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    LODGING = "lodging"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


# --- Models ---
class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = ({"sqlite_autoincrement": True},)

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    email: str = Field(max_length=255, unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Group(SQLModel, table=True):
    __tablename__ = "groups"
    __table_args__ = ({"sqlite_autoincrement": True},)

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    owner_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GroupMember(SQLModel, table=True):
    """User membership in a group. Unique (group_id, user_id)."""
    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_member"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="groups.id")
    user_id: int = Field(foreign_key="users.id")
    role: MemberRole = Field(default=MemberRole.MEMBER)


class Expense(SQLModel, table=True):
    __tablename__ = "expenses"
    __table_args__ = ({"sqlite_autoincrement": True},)

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="groups.id")
    payer_id: int = Field(foreign_key="users.id")
    amount: float = Field()
    currency: str = Field(default="ILS", max_length=3)
    description: str = Field(max_length=500)
    category: ExpenseCategory = Field(default=ExpenseCategory.OTHER)
    date: datetime = Field(default_factory=datetime.utcnow)


class ExpenseShare(SQLModel, table=True):
    """Per-user share of an expense. share_amount = exact amount for this user."""
    __tablename__ = "expense_shares"
    __table_args__ = ({"sqlite_autoincrement": True},)

    id: Optional[int] = Field(default=None, primary_key=True)
    expense_id: int = Field(foreign_key="expenses.id")
    user_id: int = Field(foreign_key="users.id")
    share_amount: float = Field()


