"""Expenses API with authentication and enhanced validation."""

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_active_user
from app.models import Expense, ExpenseShare, GroupMember, User
from app.schemas import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from app.services.vision_service import analyze_receipt

router = APIRouter(prefix="/expenses", tags=["expenses"])


def check_group_membership(session: Session, group_id: int, user_id: int) -> GroupMember:
    """Check if user is member of group."""
    member = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Not a member of this group"
        )
    return member


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


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add an expense. If shares omitted → equal split among all group members.
    If shares provided → must sum to amount.
    """
    # Check user is member of the group
    check_group_membership(session, expense.group_id, current_user.id)
    
    # Get group members
    members = session.exec(
        select(GroupMember).where(GroupMember.group_id == expense.group_id)
    ).all()
    if not members:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found or has no members"
        )
    member_ids = [m.user_id for m in members]

    # Validate payer is group member
    if expense.payer_id not in member_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payer must be a group member"
        )

    if expense.shares:
        shares = [(s.user_id, s.share_amount) for s in expense.shares]
        for uid, _ in shares:
            if uid not in member_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {uid} not in group"
                )
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
def upload_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a receipt image for AI scan. Returns extracted amount, description, date.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (jpeg, png, webp)"
        )
    
    try:
        MAX_SIZE = 10 * 1024 * 1024  # 10 MB
        contents = b""
        for chunk in iter(lambda: file.file.read(65536), b""):
            contents += chunk
            if len(contents) > MAX_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image too large (max 10 MB)"
                )
        result = analyze_receipt(contents)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vision analysis failed: {e}"
        )


@router.get("/", response_model=List[ExpenseResponse])
def list_expenses(
    group_id: int | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List expenses. If group_id provided, filter by group (user must be member)."""
    if group_id:
        # Check user is member of the group
        check_group_membership(session, group_id, current_user.id)
        expenses = session.exec(select(Expense).where(Expense.group_id == group_id)).all()
    else:
        # List all expenses from groups where user is member
        user_group_ids = session.exec(
            select(GroupMember.group_id).where(GroupMember.user_id == current_user.id)
        ).all()
        expenses = session.exec(
            select(Expense).where(Expense.group_id.in_(user_group_ids))
        ).all()
    return list(expenses)


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get expense by ID (user must be member of the expense's group)."""
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # Check user is member of the expense's group
    check_group_membership(session, expense.group_id, current_user.id)
    
    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update expense (only description and category, user must be payer)."""
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # Check user is member of the expense's group
    check_group_membership(session, expense.group_id, current_user.id)
    
    # Only payer can update expense
    if expense.payer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the payer can update this expense"
        )
    
    # Update fields
    if expense_update.description is not None:
        expense.description = expense_update.description
    if expense_update.category is not None:
        expense.category = expense_update.category
    
    session.add(expense)
    session.commit()
    session.refresh(expense)
    
    return expense


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete expense (only payer can delete)."""
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # Check user is member of the expense's group
    check_group_membership(session, expense.group_id, current_user.id)
    
    # Only payer can delete expense
    if expense.payer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the payer can delete this expense"
        )
    
    # Delete expense shares first
    shares = session.exec(
        select(ExpenseShare).where(ExpenseShare.expense_id == expense_id)
    ).all()
    for share in shares:
        session.delete(share)
    
    # Delete expense
    session.delete(expense)
    session.commit()
    
    return {"status": "ok", "message": "Expense deleted successfully"}
