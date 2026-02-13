import sqlite3
import os
from datetime import datetime, timedelta, timezone

# Put database in src directory for easier access and permission
DB_PATH = os.path.join(os.path.dirname(__file__), "mindharbor.db")


def get_conn():
    # Ensure directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            tokens_remaining INTEGER DEFAULT 0,
            pass_expiry TEXT DEFAULT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def get_or_create_user(user_id: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        res = dict(row)
        conn.close()
        return res
    c.execute("INSERT INTO users(user_id, tokens_remaining) VALUES (?, ?)", (user_id, 0))
    conn.commit()
    conn.close()
    return {"user_id": user_id, "tokens_remaining": 0, "pass_expiry": None}


def decrement_token(user_id: str) -> bool:
    u = get_or_create_user(user_id)
    if u.get("tokens_remaining", 0) > 0:
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE users SET tokens_remaining = tokens_remaining - 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    return False


def add_tokens(user_id: str, amount: int):
    get_or_create_user(user_id)
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET tokens_remaining = tokens_remaining + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def set_pass_expiry(user_id: str, days: int):
    expiry = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    get_or_create_user(user_id)
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET pass_expiry = ? WHERE user_id = ?", (expiry, user_id))
    conn.commit()
    conn.close()


def has_valid_pass(user_id: str) -> bool:
    u = get_or_create_user(user_id)
    expiry = u.get("pass_expiry")
    if not expiry:
        return False
    try:
        exp_dt = datetime.fromisoformat(expiry)
        return exp_dt > datetime.now(timezone.utc)
    except Exception:
        return False


if __name__ == "__main__":
    init_db()
