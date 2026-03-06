# Splitwise MVP — API Endpoints

## Users

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | /users/ | `{name, email}` | Register user |
| GET | /users/ | — | List all users |
| GET | /users/{id} | — | Get user by ID |

## Groups

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | /groups/ | `{name, owner_id}` | Create group (owner auto-added) |
| GET | /groups/ | — | List all groups |
| GET | /groups/{id} | — | Get group |
| POST | /groups/{id}/members | `{user_id, role?}` | Add member |

## Expenses

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | /expenses/ | `{group_id, payer_id, amount, description, category?, shares?}` | Add expense. Omit shares = equal split |
| GET | /expenses/?group_id=N | — | List expenses (optional filter) |

## Balance

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /balance/groups/{id}/balances | Net balance per user |
| GET | /balance/groups/{id}/settlements | Minimal transfers to settle |
