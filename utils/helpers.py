# utils/helpers.py
from google_sheet import get_worksheet, read_all_records, append_row, update_cell
from typing import Optional
import datetime

def get_user(user_id: int) -> Optional[dict]:
    """
    Return user record dict or None.
    Assumes Users sheet has headers:
    UserID | Username | Balance | Level | XP | TotalBets | LastDaily | Streak
    """
    users = read_all_records("Users")
    for u in users:
        if str(u.get("UserID")) == str(user_id):
            return u
    return None

def register_user(user_id: int, username: str, starting_balance: int = 1000):
    """
    Append a new user row, matching the current Users sheet headers.
    Expected headers include at least:
    UserID | Username | Balance | XP | Level | TotalBets | LastDaily | Streak | JoinDate
    """
    existing = get_user(user_id)
    if existing:
        return False

    ws = get_worksheet("Users")
    headers = ws.row_values(1)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Base defaults that should always exist
    base_defaults = {
        "UserID": str(user_id),
        "Username": username,
        "Balance": starting_balance,
        "XP": 0,
        "Level": 1,
        "TotalBets": 0,
        "LastDaily": "",
        "Streak": 0,
        "JoinDate": now_str,
    }
    
    # Milestone defaults - only add if columns exist
    milestone_defaults = {
        "Milestone_10000": False,
        "Milestone_20000": False,
        "Milestone_50000": False,
        "Milestone_100000": False,
        "Milestone_1000000": False,
    }
    
    # Combine defaults, prioritizing existing headers
    all_defaults = {**base_defaults, **milestone_defaults}
    
    # Build row based on existing headers
    row = []
    for col in headers:
        if col in all_defaults:
            row.append(all_defaults[col])
        else:
            row.append("")  # Empty for any additional columns
    
    append_row("Users", row)
    return True

LEVELS = [
    {"Level": 1, "XPRequired": 0,    "BonusAmount": 500,  "StreakBonus": 0,   "Description": "First level daily bonus"},
    {"Level": 2, "XPRequired": 1000, "BonusAmount": 600,  "StreakBonus": 50,  "Description": "Streak bonus included"},
    {"Level": 3, "XPRequired": 2500, "BonusAmount": 700,  "StreakBonus": 100, "Description": "Higher bonus for level 3"},
    {"Level": 4, "XPRequired": 5000, "BonusAmount": 900,  "StreakBonus": 150, "Description": "Higher bonus for level 4"},
    {"Level": 5, "XPRequired": 8000, "BonusAmount": 1200, "StreakBonus": 200, "Description": "High level daily bonus"},
]

def _get_level_info(current_xp: int):
    current = LEVELS[0]
    next_level = None
    for lvl in LEVELS:
        if current_xp >= lvl["XPRequired"]:
            current = lvl
        else:
            next_level = lvl
            break
    return current, next_level

def claim_daily_reward(user_id: int, base_reward: int = 500):
    """
    Claim daily reward for user.
    Rules:
    - Can claim once per UTC day (compares by YYYY-MM-DD).
    - Streak increments if last claim was exactly yesterday; otherwise resets to 1.
    - Updates Balance, LastDaily (YYYY-MM-DD), Streak, and DailyClaimedAt (timestamp) if column exists.
    Returns dict with keys: {claimed: bool, reason: str, balance: int, reward: int, streak: int, next_claim_in: str, xp: int, level: int, xp_gain: int}
    """
    ws = get_worksheet("Users")
    headers = ws.row_values(1)
    users = ws.get_all_records()

    # header indices
    def col_idx(name: str) -> Optional[int]:
        return headers.index(name) + 1 if name in headers else None

    col_user = col_idx("UserID")
    col_balance = col_idx("Balance")
    col_last_daily = col_idx("LastDaily")
    col_streak = col_idx("Streak")
    col_claimed_at = col_idx("DailyClaimedAt")
    col_xp = col_idx("XP")
    col_level = col_idx("Level")

    if not (col_user and col_balance and col_last_daily and col_streak and col_xp and col_level):
        return {"claimed": False, "reason": "Users sheet missing required columns", "balance": 0, "reward": 0, "streak": 0, "next_claim_in": ""}

    today = datetime.datetime.utcnow().date()
    yesterday = today - datetime.timedelta(days=1)
    now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # find user row
    for idx, u in enumerate(users, start=2):
        if str(u.get("UserID")) == str(user_id):
            balance_val = 0
            try:
                balance_val = int(u.get("Balance", 0))
            except Exception:
                balance_val = 0

            current_xp = 0
            try:
                current_xp = int(u.get("XP", 0) or 0)
            except Exception:
                current_xp = 0

            current_level = 1
            try:
                current_level = int(u.get("Level", 1) or 1)
            except Exception:
                current_level = 1

            last_daily_raw = str(u.get("LastDaily", "")).strip()
            last_daily_date = None
            if last_daily_raw:
                try:
                    last_daily_date = datetime.datetime.strptime(last_daily_raw, "%Y-%m-%d").date()
                except Exception:
                    last_daily_date = None

            # already claimed today?
            if last_daily_date == today:
                # compute next reset time (UTC midnight)
                tomorrow = today + datetime.timedelta(days=1)
                next_reset = datetime.datetime.combine(tomorrow, datetime.time.min)
                remaining = int((next_reset - datetime.datetime.utcnow()).total_seconds())
                hrs = remaining // 3600
                mins = (remaining % 3600) // 60
                secs = remaining % 60
                return {
                    "claimed": False,
                    "reason": f"Already claimed today. Next in {hrs}h {mins}m {secs}s",
                    "balance": balance_val,
                    "reward": 0,
                    "streak": int(u.get("Streak", 0) or 0),
                    "next_claim_in": f"{hrs}h {mins}m {secs}s",
                    "xp": current_xp,
                    "level": current_level,
                    "xp_gain": 0,
                }

            # streak calc
            current_streak = 0
            try:
                current_streak = int(u.get("Streak", 0) or 0)
            except Exception:
                current_streak = 0

            if last_daily_date == yesterday:
                new_streak = current_streak + 1
            else:
                new_streak = 1

            # compute reward and xp gain based on level and streak
            # level is determined by current XP before claim
            level_info, next_level_info = _get_level_info(current_xp)
            base_bonus = level_info["BonusAmount"]
            streak_bonus_per = level_info["StreakBonus"]
            # streak counts as new_streak after this claim
            pending_streak = new_streak
            streak_component = max(pending_streak - 1, 0) * streak_bonus_per
            reward_amount = base_bonus + streak_component
            # ensure minimum equals base_reward parameter
            reward_amount = max(reward_amount, base_reward)

            xp_gain = reward_amount  # XP increases according to reward (can tweak if needed)
            new_xp = current_xp + xp_gain

            # recalc level after XP gain
            new_level_info, _ = _get_level_info(new_xp)
            new_level = new_level_info["Level"]

            new_balance = balance_val + reward_amount

            # perform updates
            update_cell("Users", f"{chr(64 + col_balance)}{idx}", new_balance)
            update_cell("Users", f"{chr(64 + col_last_daily)}{idx}", today.strftime("%Y-%m-%d"))
            update_cell("Users", f"{chr(64 + col_streak)}{idx}", new_streak)
            if col_claimed_at:
                update_cell("Users", f"{chr(64 + col_claimed_at)}{idx}", now_str)
            # update XP and Level
            update_cell("Users", f"{chr(64 + col_xp)}{idx}", new_xp)
            if new_level != current_level:
                update_cell("Users", f"{chr(64 + col_level)}{idx}", new_level)

            return {
                "claimed": True,
                "reason": "OK",
                "balance": new_balance,
                "reward": reward_amount,
                "streak": new_streak,
                "next_claim_in": "24h",
                "xp": new_xp,
                "level": new_level,
                "xp_gain": xp_gain,
            }

    return {"claimed": False, "reason": "User not found", "balance": 0, "reward": 0, "streak": 0, "next_claim_in": ""}

def is_admin(user_id: int) -> bool:
    """Return True if user_id exists in Admins sheet."""
    try:
        ws = get_worksheet("Admins")
        records = ws.get_all_records()
        for r in records:
            if str(r.get("AdminID")) == str(user_id):
                return True
    except Exception:
        return False
    return False

def resolve_user_id(identifier: str) -> Optional[int]:
    """Resolve identifier (username or numeric id) to a user_id from Users sheet."""
    # numeric id
    if identifier.isdigit():
        return int(identifier)
    # strip leading @ if present
    if identifier.startswith("@"):
        identifier = identifier[1:]
    try:
        ws = get_worksheet("Users")
        records = ws.get_all_records()
        for r in records:
            if str(r.get("Username", "")).lower() == identifier.lower():
                try:
                    return int(r.get("UserID"))
                except Exception:
                    return None
    except Exception:
        return None
    return None

def add_admin(target_user_id: int, username: str = "", role: str = "admin") -> bool:
    """Add a row to Admins sheet if not present. Returns True if added or already exists."""
    try:
        ws = get_worksheet("Admins")
        records = ws.get_all_records()
        for r in records:
            if str(r.get("AdminID")) == str(target_user_id):
                return True
        # append respecting headers order if possible
        headers = ws.row_values(1)
        values = {"AdminID": str(target_user_id), "Username": username, "Role": role}
        row = [values.get(h, "") for h in headers] if headers else [str(target_user_id), username, role]
        append_row("Admins", row)
        return True
    except Exception:
        return False

def gain_xp(user_id: int, amount: int):
    """
    Add XP to a user and auto-update Level if thresholds are crossed.
    Returns dict {ok: bool, xp: int, level: int, delta: int}
    """
    if amount == 0:
        return {"ok": True, "xp": 0, "level": 0, "delta": 0}

    ws = get_worksheet("Users")
    headers = ws.row_values(1)

    def col_idx(name: str) -> Optional[int]:
        return headers.index(name) + 1 if name in headers else None

    col_user = col_idx("UserID")
    col_xp = col_idx("XP")
    col_level = col_idx("Level")
    if not (col_user and col_xp and col_level):
        return {"ok": False, "xp": 0, "level": 0, "delta": 0}

    users = ws.get_all_records()
    for idx, u in enumerate(users, start=2):
        if str(u.get("UserID")) == str(user_id):
            current_xp = 0
            try:
                current_xp = int(u.get("XP", 0) or 0)
            except Exception:
                current_xp = 0
            current_level = 1
            try:
                current_level = int(u.get("Level", 1) or 1)
            except Exception:
                current_level = 1

            new_xp = max(current_xp + amount, 0)
            update_cell("Users", f"{chr(64 + col_xp)}{idx}", new_xp)

            new_level_info, _ = _get_level_info(new_xp)
            new_level = new_level_info["Level"]
            if new_level != current_level:
                update_cell("Users", f"{chr(64 + col_level)}{idx}", new_level)

            return {"ok": True, "xp": new_xp, "level": new_level, "delta": amount}

    return {"ok": False, "xp": 0, "level": 0, "delta": 0}

def set_user_xp(user_id: int, new_xp: int):
    """
    Set absolute XP and auto-update Level accordingly.
    Returns dict {ok: bool, xp: int, level: int}
    """
    if new_xp < 0:
        new_xp = 0
    ws = get_worksheet("Users")
    headers = ws.row_values(1)

    def col_idx(name: str) -> Optional[int]:
        return headers.index(name) + 1 if name in headers else None

    col_user = col_idx("UserID")
    col_xp = col_idx("XP")
    col_level = col_idx("Level")
    if not (col_user and col_xp and col_level):
        return {"ok": False, "xp": 0, "level": 0}

    users = ws.get_all_records()
    for idx, u in enumerate(users, start=2):
        if str(u.get("UserID")) == str(user_id):
            update_cell("Users", f"{chr(64 + col_xp)}{idx}", new_xp)
            new_level_info, _ = _get_level_info(new_xp)
            new_level = new_level_info["Level"]
            update_cell("Users", f"{chr(64 + col_level)}{idx}", new_level)
            return {"ok": True, "xp": new_xp, "level": new_level}
    return {"ok": False, "xp": 0, "level": 0}

# ===================== Loans =====================
def get_active_loan(user_id: int) -> Optional[dict]:
    """Return the most recent active loan for the user from Logs_Loan, or None."""
    try:
        ws = get_worksheet("Logs_Loan")
        records = ws.get_all_records()
        active = [r for r in records if str(r.get("UserID")) == str(user_id) and str(r.get("Status", "")).lower() == "active"]
        if not active:
            return None
        return active[-1]
    except Exception:
        return None

def create_loan(user_id: int, amount: int, interest_rate: float = 0.1, days_until_due: int = 7) -> dict:
    """
    Create a loan entry in Logs_Loan and credit user's balance by amount.
    Returns {ok: bool, reason: str, loan: dict, new_balance: int}
    """
    if amount <= 0:
        return {"ok": False, "reason": "Amount must be > 0"}
    # prevent multiple active loans
    if get_active_loan(user_id):
        return {"ok": False, "reason": "Active loan exists"}

    user = get_user(user_id)
    if not user:
        return {"ok": False, "reason": "User not found"}

    now = datetime.datetime.utcnow()
    loan_id = f"LN-{now.strftime('%Y%m%d%H%M%S')}"
    due_date = (now + datetime.timedelta(days=days_until_due)).strftime("%Y-%m-%d")
    repay_amount = int(round(amount * (1 + interest_rate)))
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    # append loan row
    row = [loan_id, str(user_id), amount, interest_rate, due_date, repay_amount, "Active", timestamp]
    append_row("Logs_Loan", row)

    # credit balance
    try:
        current_balance = int(user.get("Balance", 0) or 0)
    except Exception:
        current_balance = 0
    new_balance = current_balance + amount
    update_user_balance(user_id, new_balance)

    return {"ok": True, "loan": {"LoanID": loan_id, "UserID": str(user_id), "Amount": amount, "InterestRate": interest_rate, "DueDate": due_date, "RepayAmount": repay_amount, "Status": "Active", "Timestamp": timestamp}, "new_balance": new_balance}

def repay_active_loan(user_id: int) -> dict:
    """
    Repay the active loan in full if balance is sufficient. Updates Logs_Loan Status to Paid.
    Returns {ok: bool, reason: str, new_balance: int, loan: dict}
    """
    user = get_user(user_id)
    if not user:
        return {"ok": False, "reason": "User not found"}

    ws = get_worksheet("Logs_Loan")
    headers = ws.row_values(1)

    def col_idx(name: str) -> Optional[int]:
        return headers.index(name) + 1 if name in headers else None

    col_status = col_idx("Status")
    col_timestamp = col_idx("Timestamp")

    records = ws.get_all_records()
    target_row_idx = None
    loan_record = None
    for idx, r in enumerate(records, start=2):
        if str(r.get("UserID")) == str(user_id) and str(r.get("Status", "")).lower() == "active":
            target_row_idx = idx
            loan_record = r
    if not loan_record or not target_row_idx:
        return {"ok": False, "reason": "No active loan"}

    try:
        balance_val = int(user.get("Balance", 0) or 0)
        repay_amount = int(loan_record.get("RepayAmount", 0) or 0)
    except Exception:
        return {"ok": False, "reason": "Invalid numbers"}

    if balance_val < repay_amount:
        return {"ok": False, "reason": "Insufficient balance"}

    new_balance = balance_val - repay_amount
    update_user_balance(user_id, new_balance)

    # mark loan as Paid
    if col_status:
        update_cell("Logs_Loan", f"{chr(64 + col_status)}{target_row_idx}", "Paid")
    if col_timestamp:
        update_cell("Logs_Loan", f"{chr(64 + col_timestamp)}{target_row_idx}", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

    loan_record["Status"] = "Paid"
    return {"ok": True, "new_balance": new_balance, "loan": loan_record}

def list_loans(user_id: int, limit: int = 5) -> list:
    """Return up to `limit` recent loans for a user from Logs_Loan (most recent last)."""
    try:
        ws = get_worksheet("Logs_Loan")
        records = ws.get_all_records()
        user_loans = [r for r in records if str(r.get("UserID")) == str(user_id)]
        return user_loans[-limit:]
    except Exception:
        return []

def update_user_balance(user_id: int, new_balance: int):
    """
    Find the user row index and update Balance column (C).
    Users sheet header is expected on row 1; data starts row 2.
    """
    ws = get_worksheet("Users")
    users = ws.get_all_records()
    for idx, u in enumerate(users, start=2):
        if str(u.get("UserID")) == str(user_id):
            # Balance column is C -> cell C{idx}
            update_cell("Users", f"C{idx}", new_balance)
            return True
    return False

def update_user_field(user_id: int, field: str, value):
    """
    Update a specific field (column) for the given user_id in Users sheet.
    Example: update_user_field(12345, "TotalBets", 5000)
    """
    ws = get_worksheet("Users")
    headers = ws.row_values(1)  # first row = header row
    if field not in headers:
        # For milestone fields, try to add the column if it doesn't exist
        if field.startswith("Milestone_"):
            try:
                # Add the milestone column to the sheet
                col_letter = chr(64 + len(headers) + 1)  # Next column
                cell_ref = f"{col_letter}1"  # Header row
                update_cell("Users", cell_ref, field)
                print(f"Added milestone column: {field}")
                
                # Update headers list
                headers.append(field)
            except Exception as e:
                print(f"Could not add milestone column {field}: {e}")
                return False
        else:
            print(f"[ERROR] Field '{field}' not found in sheet headers.")
            return False

    col_index = headers.index(field) + 1
    users = ws.get_all_records()
    for idx, u in enumerate(users, start=2):
        if str(u.get("UserID")) == str(user_id):
            cell_ref = f"{chr(64 + col_index)}{idx}"  # e.g. F2
            update_cell("Users", cell_ref, value)
            return True
    return False
