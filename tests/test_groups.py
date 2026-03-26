"""
Groups API tests with authentication.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.database import get_session, init_db
from app.models import User, Group, GroupMember, MemberRole
from app.auth import get_password_hash

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Setup test database for each test."""
    init_db()
    yield


def get_test_session():
    """Get test database session."""
    return next(get_session())


def create_test_user(name: str, email: str, password: str = "testpass123") -> dict:
    """Create a test user and return user data with token."""
    user_data = {
        "name": name,
        "email": email,
        "password": password
    }
    
    # Register user
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Login to get token
    login_response = client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_response.status_code == 200
    
    token = login_response.json()["access_token"]
    user_info = response.json()
    
    return {
        "user": user_info,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


class TestGroups:
    """Test groups API with authentication."""
    
    def test_create_group_success(self):
        """Test successful group creation."""
        user = create_test_user("Test User", "test@example.com")
        
        group_data = {"name": "Test Group"}
        response = client.post("/groups/", json=group_data, headers=user["headers"])
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Test Group"
        assert data["owner_id"] == user["user"]["id"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_group_unauthorized(self):
        """Test group creation without authentication."""
        group_data = {"name": "Test Group"}
        response = client.post("/groups/", json=group_data)
        assert response.status_code == 401
    
    def test_create_group_invalid_name(self):
        """Test group creation with invalid name."""
        user = create_test_user("Test User", "test@example.com")
        
        invalid_names = ["", "a", "<script>alert('xss')</script>", "a" * 300]
        
        for invalid_name in invalid_names:
            group_data = {"name": invalid_name}
            response = client.post("/groups/", json=group_data, headers=user["headers"])
            assert response.status_code == 422
    
    def test_list_groups_success(self):
        """Test listing groups as authenticated user."""
        user = create_test_user("Test User", "test@example.com")
        
        # Create a group first
        group_data = {"name": "Test Group"}
        client.post("/groups/", json=group_data, headers=user["headers"])
        
        # List groups
        response = client.get("/groups/", headers=user["headers"])
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Group"
    
    def test_list_groups_unauthorized(self):
        """Test listing groups without authentication."""
        response = client.get("/groups/")
        assert response.status_code == 401
    
    def test_get_group_success(self):
        """Test getting a specific group."""
        user = create_test_user("Test User", "test@example.com")
        
        # Create a group
        group_data = {"name": "Test Group"}
        create_response = client.post("/groups/", json=group_data, headers=user["headers"])
        group_id = create_response.json()["id"]
        
        # Get group
        response = client.get(f"/groups/{group_id}", headers=user["headers"])
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test Group"
        assert data["id"] == group_id
    
    def test_get_group_not_member(self):
        """Test getting a group user is not member of."""
        user1 = create_test_user("Test User 1", "test1@example.com")
        user2 = create_test_user("Test User 2", "test2@example.com")
        
        # Create group as user1
        group_data = {"name": "Test Group"}
        create_response = client.post("/groups/", json=group_data, headers=user1["headers"])
        group_id = create_response.json()["id"]
        
        # Try to get group as user2 (not a member)
        response = client.get(f"/groups/{group_id}", headers=user2["headers"])
        assert response.status_code == 403
    
    def test_add_member_success(self):
        """Test adding a member to group."""
        owner = create_test_user("Owner", "owner@example.com")
        member = create_test_user("Member", "member@example.com")
        
        # Create group
        group_data = {"name": "Test Group"}
        create_response = client.post("/groups/", json=group_data, headers=owner["headers"])
        group_id = create_response.json()["id"]
        
        # Add member
        add_data = {"user_id": member["user"]["id"], "role": "member"}
        response = client.post(f"/groups/{group_id}/members", json=add_data, headers=owner["headers"])
        assert response.status_code == 200
        
        data = response.json()
        assert "added to group" in data["message"]
    
    def test_add_member_unauthorized(self):
        """Test adding member without authentication."""
        response = client.post("/groups/1/members", json={"user_id": 1})
        assert response.status_code == 401
    
    def test_add_member_not_owner(self):
        """Test adding member by non-owner."""
        owner = create_test_user("Owner", "owner@example.com")
        member1 = create_test_user("Member 1", "member1@example.com")
        member2 = create_test_user("Member 2", "member2@example.com")
        
        # Create group as owner
        group_data = {"name": "Test Group"}
        create_response = client.post("/groups/", json=group_data, headers=owner["headers"])
        group_id = create_response.json()["id"]
        
        # Add member1
        add_data = {"user_id": member1["user"]["id"], "role": "member"}
        client.post(f"/groups/{group_id}/members", json=add_data, headers=owner["headers"])
        
        # Try to add member2 as member1 (not owner)
        add_data2 = {"user_id": member2["user"]["id"], "role": "member"}
        response = client.post(f"/groups/{group_id}/members", json=add_data2, headers=member1["headers"])
        assert response.status_code == 403
    
    def test_remove_member_success(self):
        """Test removing a member from group."""
        owner = create_test_user("Owner", "owner@example.com")
        member = create_test_user("Member", "member@example.com")
        
        # Create group
        group_data = {"name": "Test Group"}
        create_response = client.post("/groups/", json=group_data, headers=owner["headers"])
        group_id = create_response.json()["id"]
        
        # Add member
        add_data = {"user_id": member["user"]["id"], "role": "member"}
        client.post(f"/groups/{group_id}/members", json=add_data, headers=owner["headers"])
        
        # Remove member
        response = client.delete(f"/groups/{group_id}/members/{member['user']['id']}", headers=owner["headers"])
        assert response.status_code == 200
        
        data = response.json()
        assert "removed from group" in data["message"]
    
    def test_remove_member_not_owner(self):
        """Test removing member by non-owner."""
        owner = create_test_user("Owner", "owner@example.com")
        member1 = create_test_user("Member 1", "member1@example.com")
        member2 = create_test_user("Member 2", "member2@example.com")
        
        # Create group as owner
        group_data = {"name": "Test Group"}
        create_response = client.post("/groups/", json=group_data, headers=owner["headers"])
        group_id = create_response.json()["id"]
        
        # Add members
        add_data1 = {"user_id": member1["user"]["id"], "role": "member"}
        add_data2 = {"user_id": member2["user"]["id"], "role": "member"}
        client.post(f"/groups/{group_id}/members", json=add_data1, headers=owner["headers"])
        client.post(f"/groups/{group_id}/members", json=add_data2, headers=owner["headers"])
        
        # Try to remove member2 as member1 (not owner)
        response = client.delete(f"/groups/{group_id}/members/{member2['user']['id']}", headers=member1["headers"])
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
