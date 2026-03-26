"""
Expenses API tests with authentication.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.database import get_session, init_db
from app.models import User, Group, GroupMember, Expense, ExpenseShare, MemberRole
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


def create_test_group(owner: dict, name: str = "Test Group") -> dict:
    """Create a test group."""
    group_data = {"name": name}
    response = client.post("/groups/", json=group_data, headers=owner["headers"])
    assert response.status_code == 201
    
    return response.json()


def add_group_member(group_id: int, owner: dict, member: dict):
    """Add a member to a group."""
    add_data = {"user_id": member["user"]["id"], "role": "member"}
    response = client.post(f"/groups/{group_id}/members", json=add_data, headers=owner["headers"])
    assert response.status_code == 200


class TestExpenses:
    """Test expenses API with authentication."""
    
    def test_create_expense_equal_split_success(self):
        """Test successful expense creation with equal split."""
        owner = create_test_user("Owner", "owner@example.com")
        member = create_test_user("Member", "member@example.com")
        
        # Create group and add member
        group = create_test_group(owner)
        add_group_member(group["id"], owner, member)
        
        # Create expense with equal split
        expense_data = {
            "group_id": group["id"],
            "payer_id": owner["user"]["id"],
            "amount": 100.0,
            "description": "Test expense",
            "category": "food"
        }
        
        response = client.post("/expenses/", json=expense_data, headers=owner["headers"])
        assert response.status_code == 201
        
        data = response.json()
        assert data["amount"] == 100.0
        assert data["description"] == "Test expense"
        assert data["category"] == "food"
    
    def test_create_expense_manual_split_success(self):
        """Test successful expense creation with manual split."""
        owner = create_test_user("Owner", "owner@example.com")
        member = create_test_user("Member", "member@example.com")
        
        # Create group and add member
        group = create_test_group(owner)
        add_group_member(group["id"], owner, member)
        
        # Create expense with manual split
        expense_data = {
            "group_id": group["id"],
            "payer_id": owner["user"]["id"],
            "amount": 100.0,
            "description": "Test expense",
            "category": "food",
            "shares": [
                {"user_id": owner["user"]["id"], "share_amount": 60.0},
                {"user_id": member["user"]["id"], "share_amount": 40.0}
            ]
        }
        
        response = client.post("/expenses/", json=expense_data, headers=owner["headers"])
        assert response.status_code == 201
        
        data = response.json()
        assert data["amount"] == 100.0
        assert data["description"] == "Test expense"
    
    def test_create_expense_unauthorized(self):
        """Test expense creation without authentication."""
        expense_data = {
            "group_id": 1,
            "payer_id": 1,
            "amount": 100.0,
            "description": "Test expense"
        }
        
        response = client.post("/expenses/", json=expense_data)
        assert response.status_code == 401
    
    def test_create_expense_invalid_shares_sum(self):
        """Test expense creation with shares that don't sum to amount."""
        owner = create_test_user("Owner", "owner@example.com")
        member = create_test_user("Member", "member@example.com")
        
        # Create group and add member
        group = create_test_group(owner)
        add_group_member(group["id"], owner, member)
        
        # Create expense with incorrect share sum
        expense_data = {
            "group_id": group["id"],
            "payer_id": owner["user"]["id"],
            "amount": 100.0,
            "description": "Test expense",
            "shares": [
                {"user_id": owner["user"]["id"], "share_amount": 60.0},
                {"user_id": member["user"]["id"], "share_amount": 30.0}  # Sum = 90, not 100
            ]
        }
        
        response = client.post("/expenses/", json=expense_data, headers=owner["headers"])
        assert response.status_code == 422
    
    def test_create_expense_payer_not_member(self):
        """Test expense creation with payer not in group."""
        owner = create_test_user("Owner", "owner@example.com")
        non_member = create_test_user("Non Member", "nonmember@example.com")
        
        # Create group
        group = create_test_group(owner)
        
        # Try to create expense with non-member as payer
        expense_data = {
            "group_id": group["id"],
            "payer_id": non_member["user"]["id"],
            "amount": 100.0,
            "description": "Test expense"
        }
        
        response = client.post("/expenses/", json=expense_data, headers=owner["headers"])
        assert response.status_code == 400
    
    def test_create_expense_invalid_amount(self):
        """Test expense creation with invalid amount."""
        owner = create_test_user("Owner", "owner@example.com")
        
        # Create group
        group = create_test_group(owner)
        
        invalid_amounts = [-100, 0, 1000001]  # Negative, zero, over limit
        
        for amount in invalid_amounts:
            expense_data = {
                "group_id": group["id"],
                "payer_id": owner["user"]["id"],
                "amount": amount,
                "description": "Test expense"
            }
            
            response = client.post("/expenses/", json=expense_data, headers=owner["headers"])
            assert response.status_code == 422
    
    def test_list_expenses_success(self):
        """Test listing expenses for a group."""
        owner = create_test_user("Owner", "owner@example.com")
        member = create_test_user("Member", "member@example.com")
        
        # Create group and add member
        group = create_test_group(owner)
        add_group_member(group["id"], owner, member)
        
        # Create expense
        expense_data = {
            "group_id": group["id"],
            "payer_id": owner["user"]["id"],
            "amount": 100.0,
            "description": "Test expense"
        }
        client.post("/expenses/", json=expense_data, headers=owner["headers"])
        
        # List expenses for group
        response = client.get(f"/expenses/?group_id={group['id']}", headers=owner["headers"])
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["description"] == "Test expense"
    
    def test_list_expenses_unauthorized(self):
        """Test listing expenses without authentication."""
        response = client.get("/expenses/")
        assert response.status_code == 401
    
    def test_get_expense_success(self):
        """Test getting a specific expense."""
        owner = create_test_user("Owner", "owner@example.com")
        
        # Create group and expense
        group = create_test_group(owner)
        expense_data = {
            "group_id": group["id"],
            "payer_id": owner["user"]["id"],
            "amount": 100.0,
            "description": "Test expense"
        }
        create_response = client.post("/expenses/", json=expense_data, headers=owner["headers"])
        expense_id = create_response.json()["id"]
        
        # Get expense
        response = client.get(f"/expenses/{expense_id}", headers=owner["headers"])
        assert response.status_code == 200
        
        data = response.json()
        assert data["description"] == "Test expense"
        assert data["amount"] == 100.0
    
    def test_get_expense_not_member(self):
        """Test getting expense from group user is not member of."""
        owner = create_test_user("Owner", "owner@example.com")
        non_member = create_test_user("Non Member", "nonmember@example.com")
        
        # Create group and expense as owner
        group = create_test_group(owner)
        expense_data = {
            "group_id": group["id"],
            "payer_id": owner["user"]["id"],
            "amount": 100.0,
            "description": "Test expense"
        }
        create_response = client.post("/expenses/", json=expense_data, headers=owner["headers"])
        expense_id = create_response.json()["id"]
        
        # Try to get expense as non-member
        response = client.get(f"/expenses/{expense_id}", headers=non_member["headers"])
        assert response.status_code == 403
    
    def test_update_expense_success(self):
        """Test updating an expense."""
        owner = create_test_user("Owner", "owner@example.com")
        
        # Create group and expense
        group = create_test_group(owner)
        expense_data = {
            "group_id": group["id"],
            "payer_id": owner["user"]["id"],
            "amount": 100.0,
            "description": "Test expense",
            "category": "food"
        }
        create_response = client.post("/expenses/", json=expense_data, headers=owner["headers"])
        expense_id = create_response.json()["id"]
        
        # Update expense
        update_data = {
            "description": "Updated expense",
            "category": "transport"
        }
        response = client.put(f"/expenses/{expense_id}", json=update_data, headers=owner["headers"])
        assert response.status_code == 200
        
        data = response.json()
        assert data["description"] == "Updated expense"
        assert data["category"] == "transport"
    
    def test_update_expense_not_payer(self):
        """Test updating expense by non-payer."""
        owner = create_test_user("Owner", "owner@example.com")
        member = create_test_user("Member", "member@example.com")
        
        # Create group and add member
        group = create_test_group(owner)
        add_group_member(group["id"], owner, member)
        
        # Create expense as owner
        expense_data = {
            "group_id": group["id"],
            "payer_id": owner["user"]["id"],
            "amount": 100.0,
            "description": "Test expense"
        }
        create_response = client.post("/expenses/", json=expense_data, headers=owner["headers"])
        expense_id = create_response.json()["id"]
        
        # Try to update expense as member (not payer)
        update_data = {"description": "Updated expense"}
        response = client.put(f"/expenses/{expense_id}", json=update_data, headers=member["headers"])
        assert response.status_code == 403
    
    def test_delete_expense_success(self):
        """Test deleting an expense."""
        owner = create_test_user("Owner", "owner@example.com")
        
        # Create group and expense
        group = create_test_group(owner)
        expense_data = {
            "group_id": group["id"],
            "payer_id": owner["user"]["id"],
            "amount": 100.0,
            "description": "Test expense"
        }
        create_response = client.post("/expenses/", json=expense_data, headers=owner["headers"])
        expense_id = create_response.json()["id"]
        
        # Delete expense
        response = client.delete(f"/expenses/{expense_id}", headers=owner["headers"])
        assert response.status_code == 200
        
        data = response.json()
        assert "deleted successfully" in data["message"]
    
    def test_delete_expense_not_payer(self):
        """Test deleting expense by non-payer."""
        owner = create_test_user("Owner", "owner@example.com")
        member = create_test_user("Member", "member@example.com")
        
        # Create group and add member
        group = create_test_group(owner)
        add_group_member(group["id"], owner, member)
        
        # Create expense as owner
        expense_data = {
            "group_id": group["id"],
            "payer_id": owner["user"]["id"],
            "amount": 100.0,
            "description": "Test expense"
        }
        create_response = client.post("/expenses/", json=expense_data, headers=owner["headers"])
        expense_id = create_response.json()["id"]
        
        # Try to delete expense as member (not payer)
        response = client.delete(f"/expenses/{expense_id}", headers=member["headers"])
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
