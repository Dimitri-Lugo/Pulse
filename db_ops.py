import sqlite3
import os
import time
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pulse.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            token TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    hashed = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return False
    pw_hash = row["password_hash"]
    if pw_hash.startswith(("$2b$", "$2a$", "$2y$")):
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode("utf-8"), pw_hash.encode("utf-8"))
        except Exception:
            return False
    return check_password_hash(pw_hash, password)

def store_reset_token(email: str, token: str, expires_in: int = 900):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM password_reset_tokens WHERE expires_at < ?", (time.time(),))
    cursor.execute("INSERT OR REPLACE INTO password_reset_tokens (token, email, expires_at) VALUES (?, ?, ?)",
                   (token, email, time.time() + expires_in))
    conn.commit()
    conn.close()

def verify_reset_token(token: str):
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT email FROM password_reset_tokens WHERE token = ? AND expires_at > ?",
                         (token, time.time())).fetchone()
    conn.close()
    return row["email"] if row else None

def consume_reset_token(token: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM password_reset_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def update_password(email: str, new_password: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                   (generate_password_hash(new_password), email))
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def add_asset(user_id, ticker, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO portfolios (user_id, ticker, amount) VALUES (?, ?, ?)", (user_id, ticker, amount))
    conn.commit()
    conn.close()

def get_portfolio(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker, amount FROM portfolios WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
