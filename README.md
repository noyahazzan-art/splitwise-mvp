# Splitwise MVP

Expense splitting & balance settlement — FastAPI + SQLite + SQLModel.

## Quick Start

```powershell
cd C:\Users\nchma\CascadeProjects\splitwise
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\run.ps1
```

API: http://localhost:8001
Docs: http://localhost:8001/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /users/ | Register user |
| GET | /users/ | List users |
| GET | /users/{id} | Get user |
| POST | /groups/ | Create group |
| GET | /groups/ | List groups |
| POST | /groups/{id}/members | Add member |
| POST | /expenses/ | Add expense (equal or manual split) |
| GET | /expenses/?group_id=N | List expenses |
| GET | /balance/groups/{id}/balances | Net balance per user |
| GET | /balance/groups/{id}/settlements | Minimal transfers |

## Data Model

- **User**: name, email (unique)
- **Group**: name, owner_id
- **GroupMember**: group_id, user_id (unique pair)
- **Expense**: group_id, payer_id, amount, description, category
- **ExpenseShare**: expense_id, user_id, share_amount

## Requirements

See [REQUIREMENTS.md](REQUIREMENTS.md).
