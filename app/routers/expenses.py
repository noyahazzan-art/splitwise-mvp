"""Expenses API."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, select

from app.database import get_session
from app.models import Expense, ExpenseShare, GroupMember
from app.schemas import ExpenseCreate, ExpenseResponse
from app.services.vision_service import analyze_receipt

router = APIRouter(prefix="/expenses", tags=["expenses"])

UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _create_expense_with_shares(
    session: Session,
    exp: ExpenseCreate,
    shares: list[tuple[int, float]],
) -> Expense:
    """Create expense and expense shares."""
    db_exp = Expense(
        group_id=exp.group_id,
        payer_id=exp.payer_id,
        amount=exp.amount,
        currency=exp.currency,
        description=exp.description,
        category=exp.category,
    )
    session.add(db_exp)
    session.commit()
    session.refresh(db_exp)
    for user_id, share_amt in shares:
        session.add(ExpenseShare(expense_id=db_exp.id, user_id=user_id, share_amount=share_amt))
    session.commit()
    return db_exp


@router.post("/", response_model=ExpenseResponse)
def create_expense(expense: ExpenseCreate, session: Session = Depends(get_session)):
    """
    Add an expense. If shares omitted → equal split among all group members.
    If shares provided → must sum to amount.
    """
    members = session.exec(
        select(GroupMember).where(GroupMember.group_id == expense.group_id)
    ).all()
    if not members:
        raise HTTPException(status_code=404, detail="Group not found or has no members")
    member_ids = [m.user_id for m in members]

    if expense.payer_id not in member_ids:
        raise HTTPException(status_code=400, detail="Payer must be a group member")

    if expense.shares:
        total = sum(s.share_amount for s in expense.shares)
        if abs(total - expense.amount) > 0.01:
            raise HTTPException(status_code=400, detail="Shares must sum to amount")
        shares = [(s.user_id, s.share_amount) for s in expense.shares]
        for uid, _ in shares:
            if uid not in member_ids:
                raise HTTPException(status_code=400, detail=f"User {uid} not in group")
    else:
        # Equal split
        n = len(member_ids)
        each = round(expense.amount / n, 2)
        remainder = expense.amount - each * n
        shares = []
        for i, uid in enumerate(member_ids):
            amt = each + (remainder if i == 0 else 0)
            shares.append((uid, round(amt, 2)))

    db_exp = _create_expense_with_shares(session, expense, shares)
    return db_exp


@router.post("/upload")
def upload_receipt(file: UploadFile = File(...)):
    """
    Upload a receipt image for AI scan. Returns extracted amount, description, date.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (jpeg, png, webp)")
    try:
        contents = file.file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10 MB
            raise HTTPException(status_code=400, detail="Image too large (max 10 MB)")
        result = analyze_receipt(contents)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {e}")


@router.get("/", response_model=list[ExpenseResponse])
def list_expenses(group_id: int | None = None, session: Session = Depends(get_session)):
    """List expenses. If group_id provided, filter by group."""
    if group_id:
        expenses = session.exec(select(Expense).where(Expense.group_id == group_id)).all()
    else:
        expenses = session.exec(select(Expense)).all()
    return list(expenses)
