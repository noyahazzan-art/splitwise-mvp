"""
Balance & Settlement Logic — "מי חייב למי".

Computes net balance per user in a group, then simplifies to minimal transfers.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING

from sqlmodel import Session, select

if TYPE_CHECKING:
    from app.models import Expense, ExpenseShare, GroupMember, User

log = logging.getLogger(__name__)
TOLERANCE = 0.01


def compute_net_balances(
    expenses: list,
    shares_by_expense: dict[int, list],
) -> dict[int, float]:
    """
    For each user_id: net = (paid) - (share).
    Positive = others owe them. Negative = they owe others.
    """
    net: dict[int, float] = defaultdict(float)
    for exp in expenses:
        payer_id = exp.payer_id
        amount = exp.amount
        net[payer_id] += amount
        for share in shares_by_expense.get(exp.id, []):
            net[share.user_id] -= share.share_amount
    return dict(net)


def calculate_net_balances(session: Session, group_id: int) -> dict[int, float]:
    """
    Fetch all expenses and shares for the group, compute net balance per user.
    Total Paid - Total Owed per user. Positive = creditor, negative = debtor.
    Validates that sum of net balances is zero (data integrity).
    """
    from app.models import Expense, ExpenseShare

    expenses = list(session.exec(select(Expense).where(Expense.group_id == group_id)).all())
    shares_by_expense: dict[int, list] = {}
    for exp in expenses:
        shares = list(
            session.exec(select(ExpenseShare).where(ExpenseShare.expense_id == exp.id)).all()
        )
        shares_by_expense[exp.id] = shares

    net = compute_net_balances(expenses, shares_by_expense)

    total = sum(net.values())
    if abs(total) > TOLERANCE:
        log.error(
            "Data integrity violation: group_id=%d net sum=%.4f (expected 0). Money leak in calculations.",
            group_id,
            total,
        )

    return net


def simplify_debts(net_balances: dict[int, float]) -> list[dict]:
    """
    Greedy settlement: match biggest creditor with biggest debtor.
    Minimizes number of transactions to settle all debts.
    Returns list of {"from_user": id, "to_user": id, "amount": x}.
    """
    creditors = [(u, b) for u, b in net_balances.items() if b > TOLERANCE]
    debtors = [(u, -b) for u, b in net_balances.items() if b < -TOLERANCE]
    creditors.sort(key=lambda x: -x[1])
    debtors.sort(key=lambda x: -x[1])

    transfers: list[dict] = []
    i, j = 0, 0
    while i < len(creditors) and j < len(debtors):
        cred_id, cred_amt = creditors[i]
        debt_id, debt_amt = debtors[j]
        settle = min(cred_amt, debt_amt)
        if settle > TOLERANCE:
            transfers.append({
                "from_user": debt_id,
                "to_user": cred_id,
                "amount": round(settle, 2),
            })
        creditors[i] = (cred_id, cred_amt - settle)
        debtors[j] = (debt_id, debt_amt - settle)
        if creditors[i][1] < TOLERANCE:
            i += 1
        if debtors[j][1] < TOLERANCE:
            j += 1
    return transfers
