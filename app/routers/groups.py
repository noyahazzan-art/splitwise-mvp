"""Groups API with authentication and authorization."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_active_user
from app.models import Group, GroupMember, MemberRole, User
from app.schemas import GroupAddMember, GroupCreate, GroupResponse

router = APIRouter(prefix="/groups", tags=["groups"])


def check_group_membership(session: Session, group_id: int, user_id: int | None) -> GroupMember:
    """Check if user is member of group and return member record."""
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


def check_group_ownership(session: Session, group_id: int, user_id: int | None) -> GroupMember:
    """Check if user is owner of group and return member record."""
    member = check_group_membership(session, group_id, user_id)
    if member.role != MemberRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only group owners can perform this action"
        )
    return member


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    group: GroupCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Create a group. Current user becomes owner and is auto-added as first member."""
    db_group = Group(name=group.name, owner_id=current_user.id)
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    
    # Add owner as member
    session.add(GroupMember(group_id=db_group.id, user_id=current_user.id, role=MemberRole.OWNER))
    session.commit()
    return db_group


@router.get("/", response_model=List[GroupResponse])
def list_groups(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List groups where current user is a member."""
    member_groups = session.exec(
        select(Group).join(GroupMember).where(GroupMember.user_id == current_user.id)
    ).all()
    return list(member_groups)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get group by ID (only if user is member)."""
    check_group_membership(session, group_id, current_user.id)
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    return group


@router.post("/{group_id}/members")
def add_member(
    group_id: int,
    member: GroupAddMember,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Add a user to a group. Only group owners can add members."""
    # Check if current user is owner
    check_group_ownership(session, group_id, current_user.id)
    
    # Validate group exists
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Validate target user exists
    user = session.get(User, member.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is already member
    existing = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == member.user_id,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already in group"
        )
    
    session.add(GroupMember(group_id=group_id, user_id=member.user_id, role=member.role))
    session.commit()
    return {"status": "ok", "message": f"User {member.user_id} added to group"}


@router.delete("/{group_id}/members/{user_id}")
def remove_member(
    group_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a member from group. Only owners can remove members."""
    # Check if current user is owner
    check_group_ownership(session, group_id, current_user.id)
    
    # Cannot remove the owner
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove group owner. Transfer ownership first."
        )
    
    # Find and remove member
    member = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in group"
        )
    
    session.delete(member)
    session.commit()
    return {"status": "ok", "message": f"User {user_id} removed from group"}
