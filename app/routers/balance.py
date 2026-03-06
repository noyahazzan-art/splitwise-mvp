"""Balance & Settlement API."""

from fastapi import APIRouter, Depends, HTTPException

from app.balance import calculate_net_balances, simplify_debts
from app.database import get_session
from app.models import Group
from app.schemas import BalanceEntry, SettlementEntry
from sqlmodel import Session

router = APIRouter(prefix="/balance", tags=["balance"])


@router.get("/groups/{group_id}/balances", response_model=list[BalanceEntry])
def get_group_balances(group_id: int, session: Session = Depends(get_session)):
    """Net balance per user in group. Positive = owed to them, negative = they owe."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    net = calculate_net_balances(session, group_id)
    return [BalanceEntry(user_id=uid, balance=round(b, 2)) for uid, b in net.items()]


@router.get("/groups/{group_id}/settle", response_model=list[SettlementEntry])
def get_group_settle(group_id: int, session: Session = Depends(get_session)):
    """Optimized settlement: minimal transfers to balance all debts."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    net = calculate_net_balances(session, group_id)
    transfers = simplify_debts(net)
    return [
        SettlementEntry(
            from_user_id=t["from_user"],
            to_user_id=t["to_user"],
            amount=t["amount"],
        )
        for t in transfers
    ]


@router.get("/groups/{group_id}/settlements", response_model=list[SettlementEntry])
def get_group_settlements(group_id: int, session: Session = Depends(get_session)):
    """Alias for /settle. Minimal transfers: who pays whom to settle all debts."""
    return get_group_settle(group_id, session)
