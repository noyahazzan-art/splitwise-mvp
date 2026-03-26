"""Balance & Settlement API with authentication."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.balance import calculate_net_balances, simplify_debts
from app.database import get_session
from app.dependencies import get_current_active_user
from app.models import Group, GroupMember, User
from app.schemas import BalanceEntry, SettlementEntry

router = APIRouter(prefix="/balance", tags=["balance"])


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


@router.get("/groups/{group_id}/balances", response_model=List[BalanceEntry])
def get_group_balances(
    group_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Net balance per user in group. Positive = owed to them, negative = they owe."""
    # Check user is member of the group
    check_group_membership(session, group_id, current_user.id)
    
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    net = calculate_net_balances(session, group_id)
    return [BalanceEntry(user_id=uid, balance=round(b, 2)) for uid, b in net.items()]


@router.get("/groups/{group_id}/settle", response_model=List[SettlementEntry])
def get_group_settle(
    group_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Optimized settlement: minimal transfers to balance all debts."""
    # Check user is member of the group
    check_group_membership(session, group_id, current_user.id)
    
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    net = calculate_net_balances(session, group_id)
    transfers = simplify_debts(net)
    return [
        SettlementEntry(
            from_user_id=t["from_user"],
            to_user_id=t["to_user"],
            amount=round(t["amount"], 2),
        )
        for t in transfers
    ]


@router.get("/groups/{group_id}/settlements", response_model=List[SettlementEntry])
def get_group_settlements(
    group_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Alias for /settle. Minimal transfers: who pays whom to settle all debts."""
    return get_group_settle(group_id, session, current_user)
