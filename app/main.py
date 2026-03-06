"""Splitwise MVP — FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.balance import calculate_net_balances, simplify_debts
from app.database import get_session, init_db
from app.models import Group, GroupMember, User
from app.routers import balance, expenses, groups, users

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Splitwise MVP",
    version="0.1.0",
    description="Expense splitting & balance settlement",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(groups.router)
app.include_router(expenses.router)
app.include_router(balance.router)


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    group_id: int | None = Query(None, description="Group to view"),
    session: Session = Depends(get_session),
):
    """Dashboard: groups, net balances, optimized settlement. Data integrity check visible."""
    groups_list = list(session.exec(select(Group)).all())
    selected_group = None
    balances = []
    settlements = []
    user_names: dict[int, str] = {}
    group_members: list[dict] = []
    net_sum = 0.0
    net_sum_ok = True

    if group_id:
        selected_group = session.get(Group, group_id)
        if selected_group:
            net = calculate_net_balances(session, group_id)
            net_sum = sum(net.values())
            net_sum_ok = abs(net_sum) < 0.01
            balances = [{"user_id": uid, "balance": round(b, 2)} for uid, b in net.items()]
            transfers = simplify_debts(net)
            settlements = [
                {"from_user_id": t["from_user"], "to_user_id": t["to_user"], "amount": t["amount"]}
                for t in transfers
            ]
            user_ids = {b["user_id"] for b in balances} | {s["from_user_id"] for s in settlements} | {s["to_user_id"] for s in settlements}
            for uid in user_ids:
                u = session.get(User, uid)
                if u:
                    user_names[uid] = u.name
            # Group members for Add Expense form
            members = session.exec(
                select(GroupMember).where(GroupMember.group_id == group_id)
            ).all()
            group_members = []
            for m in members:
                u = session.get(User, m.user_id)
                group_members.append({"user_id": m.user_id, "name": u.name if u else "?"})

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "groups": groups_list,
            "selected_group_id": group_id,
            "selected_group": selected_group,
            "balances": balances,
            "settlements": settlements,
            "user_names": user_names,
            "group_members": group_members,
            "net_sum": net_sum,
            "net_sum_ok": net_sum_ok,
        },
    )


@app.get("/api")
def root():
    return {"service": "Splitwise MVP", "docs": "/docs", "dashboard": "/dashboard"}
