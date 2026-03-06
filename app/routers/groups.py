"""Groups API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Group, GroupMember, MemberRole, User
from app.schemas import GroupAddMember, GroupCreate, GroupResponse

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("/", response_model=GroupResponse)
def create_group(group: GroupCreate, session: Session = Depends(get_session)):
    """Create a group. Owner is auto-added as first member."""
    owner = session.get(User, group.owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Owner user not found")
    db_group = Group(name=group.name, owner_id=group.owner_id)
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    # Add owner as member
    session.add(GroupMember(group_id=db_group.id, user_id=group.owner_id, role=MemberRole.OWNER))
    session.commit()
    return db_group


@router.get("/", response_model=list[GroupResponse])
def list_groups(session: Session = Depends(get_session)):
    """List all groups."""
    groups = session.exec(select(Group)).all()
    return list(groups)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: int, session: Session = Depends(get_session)):
    """Get group by ID."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.post("/{group_id}/members")
def add_member(
    group_id: int,
    member: GroupAddMember,
    session: Session = Depends(get_session),
):
    """Add a user to a group. Fails if already a member."""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    user = session.get(User, member.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    existing = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == member.user_id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already in group")
    session.add(GroupMember(group_id=group_id, user_id=member.user_id, role=member.role))
    session.commit()
    return {"status": "ok", "message": f"User {member.user_id} added to group"}
