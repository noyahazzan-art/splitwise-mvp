"""Pytest fixtures for Splitwise tests."""

import pytest
from sqlmodel import Session, create_engine, SQLModel

from app.models import Expense, ExpenseShare, Group, GroupMember, User, MemberRole


@pytest.fixture
def db_engine():
    """In-memory SQLite for tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(db_engine):
    """Fresh session per test."""
    with Session(db_engine) as s:
        yield s
