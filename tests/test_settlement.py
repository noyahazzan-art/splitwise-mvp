"""
Integration test: Debt Settlement Engine.

Scenario:
- User A pays 100 for A, B, and C (equal split: 33.33 each)
- User B pays 50 for B and C (B=25, C=25)

Expected net balances:
- A: +66.67 (paid 100, owed 33.33)
- B: -8.33 (paid 50, owed 33.33+25=58.33)
- C: -58.33 (paid 0, owed 33.33+25=58.33)

Expected minimal transfers:
- C -> A: 58.33
- B -> A: 8.33
"""

import pytest
from sqlmodel import Session

from app.balance import calculate_net_balances, simplify_debts, compute_net_balances
from app.models import Expense, ExpenseShare, Group, GroupMember, User, MemberRole, ExpenseCategory


@pytest.fixture
def scenario_abc(session):
    """Create users A,B,C, group, and expenses: A pays 100 for all, B pays 50 for B,C."""
    a = User(name="Alice", email="alice@test.com")
    b = User(name="Bob", email="bob@test.com")
    c = User(name="Carol", email="carol@test.com")
    session.add(a)
    session.add(b)
    session.add(c)
    session.commit()
    session.refresh(a)
    session.refresh(b)
    session.refresh(c)

    grp = Group(name="Test Group", owner_id=a.id)
    session.add(grp)
    session.commit()
    session.refresh(grp)

    session.add(GroupMember(group_id=grp.id, user_id=a.id, role=MemberRole.OWNER))
    session.add(GroupMember(group_id=grp.id, user_id=b.id, role=MemberRole.MEMBER))
    session.add(GroupMember(group_id=grp.id, user_id=c.id, role=MemberRole.MEMBER))
    session.commit()

    # Expense 1: A pays 100 for A, B, C (equal split)
    exp1 = Expense(
        group_id=grp.id,
        payer_id=a.id,
        amount=100.0,
        description="Dinner",
        category=ExpenseCategory.FOOD,
    )
    session.add(exp1)
    session.commit()
    session.refresh(exp1)
    session.add(ExpenseShare(expense_id=exp1.id, user_id=a.id, share_amount=100.0 / 3))
    session.add(ExpenseShare(expense_id=exp1.id, user_id=b.id, share_amount=100.0 / 3))
    session.add(ExpenseShare(expense_id=exp1.id, user_id=c.id, share_amount=100.0 / 3))

    # Expense 2: B pays 50 for B and C
    exp2 = Expense(
        group_id=grp.id,
        payer_id=b.id,
        amount=50.0,
        description="Taxi",
        category=ExpenseCategory.TRANSPORT,
    )
    session.add(exp2)
    session.commit()
    session.refresh(exp2)
    session.add(ExpenseShare(expense_id=exp2.id, user_id=b.id, share_amount=25.0))
    session.add(ExpenseShare(expense_id=exp2.id, user_id=c.id, share_amount=25.0))

    session.commit()
    return {"group_id": grp.id, "A": a.id, "B": b.id, "C": c.id}


def test_calculate_net_balances_sum_zero(session, scenario_abc):
    """Sum of all net balances must be zero (data integrity)."""
    net = calculate_net_balances(session, scenario_abc["group_id"])
    total = sum(net.values())
    assert abs(total) < 0.02, f"Net sum should be 0, got {total}"


def test_net_balances_values(session, scenario_abc):
    """Verify expected net balances for A, B, C."""
    net = calculate_net_balances(session, scenario_abc["group_id"])
    a_id, b_id, c_id = scenario_abc["A"], scenario_abc["B"], scenario_abc["C"]

    assert net[a_id] > 65, "A should be creditor (~66.67)"
    assert net[b_id] < -5, "B should be debtor (~-8.33)"
    assert net[c_id] < -55, "C should be debtor (~-58.33)"


def test_simplify_debts_minimal_transfers(session, scenario_abc):
    """Settlement should produce exactly 2 transfers: C->A, B->A."""
    net = calculate_net_balances(session, scenario_abc["group_id"])
    transfers = simplify_debts(net)

    assert len(transfers) == 2, f"Expected 2 transfers, got {len(transfers)}"

    # All transfers should go to A (the only creditor)
    a_id = scenario_abc["A"]
    for t in transfers:
        assert t["to_user"] == a_id
        assert t["from_user"] in (scenario_abc["B"], scenario_abc["C"])
        assert t["amount"] > 0

    total_settled = sum(t["amount"] for t in transfers)
    assert abs(total_settled - 66.67) < 0.02, f"Total settled ~66.67, got {total_settled}"


def test_simplify_debts_format(session, scenario_abc):
    """Transfers must have from_user, to_user, amount keys."""
    net = calculate_net_balances(session, scenario_abc["group_id"])
    transfers = simplify_debts(net)

    for t in transfers:
        assert "from_user" in t
        assert "to_user" in t
        assert "amount" in t
        assert isinstance(t["amount"], (int, float))
