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

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    """Create all tables and indexes for optimal performance."""
    SQLModel.metadata.create_all(engine)
    
    # Create performance indexes using text() for raw SQL
    from sqlalchemy import text
    with engine.connect() as conn:
        # Index for faster group lookups
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_expenses_group_id ON expenses(group_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_expense_shares_expense_id ON expense_shares(expense_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_expense_shares_user_id ON expense_shares(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_group_members_group_id ON group_members(group_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_group_members_user_id ON group_members(user_id)"))
        conn.commit()


def get_session():
    """Dependency: yield a database session."""
    with Session(engine) as session:
        yield session
