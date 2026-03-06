"""Database setup — SQLite + SQLModel."""

from pathlib import Path

from sqlmodel import Session, create_engine

from app.models import (  # noqa: F401 — register all models for create_all
    Expense,
    ExpenseShare,
    Group,
    GroupMember,
    SQLModel,
    User,
)

DB_PATH = Path(__file__).parent.parent / "data" / "splitwise.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def init_db() -> None:
    """Create all tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency: yield a database session."""
    with Session(engine) as session:
        yield session
