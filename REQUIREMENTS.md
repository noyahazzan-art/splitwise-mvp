# Splitwise MVP — Requirements Definition

**Design precedes Implementation.** מסמך דרישות לגרסה הראשונה (MVP).

**נתיב:** `C:\Users\nchma\CascadeProjects\splitwise`

---

## 1. Scope — גרסה ראשונה (MVP)

### 1.1 User Management

| דרישה | תיאור |
|-------|--------|
| **רישום משתמשים** | הרשמה עם שם ואימייל (אימות בסיסי) |
| **פרופיל בסיסי** | שדות: `name`, `email`, `created_at` |
| **מזהה ייחודי** | UUID או auto-increment ID לכל משתמש |
| **אין אימות OAuth** | MVP — אימייל ייחודי מספיק לזיהוי |

### 1.2 Groups & Members

| דרישה | תיאור |
|-------|--------|
| **יצירת קבוצה** | שם קבוצה (למשל: "טיול לצפון", "חשבונות דירה") |
| **מנהל קבוצה** | יוצר הקבוצה = owner |
| **שיוך משתמשים** | הוספת משתמשים כחברים בקבוצה |
| **חברות מרובה** | משתמש יכול להיות בכמה קבוצות |
| **מינימום חברים** | קבוצה חייבת לפחות 2 משתתפים (כולל היוצר) |

### 1.3 Expense Engine

| דרישה | תיאור |
|-------|--------|
| **הוספת הוצאה** | סכום (מטבע), תיאור, קטגוריה, תאריך |
| **משלם** | משתמש אחד ששילם את ההוצאה (payer) |
| **חלוקה** | **שווה** — חלוקה שווה בין כל המשתתפים, או **ידנית** — אחוזים/סכומים לכל משתתף |
| **קטגוריות** | רשימה קבועה (מזון, תחבורה, לינה, בידור, אחר) |
| **הוצאה בקבוצה** | הוצאה משויכת לקבוצה אחת; משתתפים = תת-קבוצה או כל חברי הקבוצה |

### 1.4 Balance & Settlement Logic

| דרישה | תיאור |
|-------|--------|
| **יתרה לכל משתמש** | בקבוצה: "X חייב Y סכום Z" או "X מקבל מ-Y סכום Z" |
| **אלגוריתם חובות** | חישוב "מי חייב למי" — מזעור מספר ההעברות (debt simplification) |
| **יתרה סופית** | לכל משתמש בקבוצה: סכום חיובי = חייבים לו, שלילי = הוא חייב |
| **סיכום קבוצה** | סיכום יתרות בתוך קבוצה; אין חובות בין קבוצות (כל קבוצה עצמאית) |

---

## 2. Tech Stack

| רכיב | בחירה | הערה |
|------|--------|------|
| **Backend** | FastAPI | התאמה עתידית ל-Agent, async, OpenAPI |
| **Database** | SQLite | פשוט, קובץ יחיד, אמין ל-MVP |
| **ORM** | SQLModel | Pydantic + SQLAlchemy, type-safe, מומלץ ל-FastAPI |

---

## 3. מודל נתונים (Data Model) — סקיצה

```
User: id, name, email, created_at
Group: id, name, owner_id, created_at
GroupMember: group_id, user_id, role (owner/member)
Expense: id, group_id, payer_id, amount, currency, description, category, date
ExpenseShare: expense_id, user_id, share_amount (או share_percent)
```

**Balance Logic:**
לכל קבוצה — סכום נטו לכל משתמש = (מה ששילם) - (מה שחלקו עליו).
אלגוריתם מזעור: המרת חובות לרשת מינימלית (למשל: A→B, B→C במקום A→B, A→C, B→C).

---

## 4. Out of Scope (MVP)

- אימות OAuth / JWT
- תשלומים אמיתיים (רק חישוב חובות)
- אפליקציית מובייל
- היסטוריית שינויים (audit log)
- מטבעות מרובים (MVP: מטבע אחד קבוע, למשל ILS)

---

## 5. דגש מבצעי — Dry Run Mode

**בזמן Dry Run של ה-Agent:**
- אם ה-Heartbeat Watchdog שולח התראה לטלגרם — **עצור מיד** את העבודה על Splitwise
- עבור לתחקור ה-Agent לפי `docs/INFRASTRUCTURE_TROUBLESHOOTING.md`

---

## 6. Implementation Status

- [x] **Database Schema** — `app/models.py` (SQLModel, UniqueConstraint)
- [x] **API Endpoints** — Users, Groups, Expenses, Balance
- [x] **Balance Logic** — `app/balance.py` (net balances + debt simplification)
- [x] **FastAPI App** — `app/main.py`, port 8001

**הרצה:** `.\run.ps1` או `uvicorn app.main:app --reload --port 8001`
