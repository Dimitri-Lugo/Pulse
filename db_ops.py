import os
import time
import secrets
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash


# Reads the database connection string from Streamlit secrets or falls back to an env variable
def _get_db_url() -> str:
    try:
        import streamlit as st
        return st.secrets["DATABASE_URL"]
    except Exception:
        return os.environ.get("DATABASE_URL", "")


# Keeps a pool of up to 10 open connections to avoid opening and closing one on every single db call
def _get_pool():
    import streamlit as st
    from psycopg2.pool import ThreadedConnectionPool

    @st.cache_resource
    def _build():
        return ThreadedConnectionPool(1, 10, _get_db_url())

    return _build()


# Wraps a pooled connection so calling .close() returns it to the pool instead of destroying it
class _PooledConn:
    def __init__(self):
        self._pool = _get_pool()
        self._conn = self._pool.getconn()

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def cursor(self, **kwargs):
        return self._conn.cursor(**kwargs)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    # Returns the connection back to the pool instead of actually closing it
    def close(self):
        self._pool.putconn(self._conn)

    @property
    def closed(self):
        return self._conn.closed


def get_connection():
    return _PooledConn()


# Returns a cursor that gives back rows as dicts — row["column"] instead of row[0]
def _cur(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# Creates all the tables if they don't exist yet — runs every time the app starts
def init_db():
    conn = get_connection()
    cur = _cur(conn)

    # Main users table — stores login info, nickname, role, and profile picture
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nickname TEXT DEFAULT '',
            role TEXT DEFAULT 'User',
            profile_pic BYTEA DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Adds columns that might not exist if the database was created before these columns were added
    for stmt in [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname TEXT DEFAULT ''",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'User'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_pic BYTEA DEFAULT NULL",
    ]:
        cur.execute(stmt)

    # Older portfolio table — not really used by the dashboard anymore but kept around just in case
    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            ticker TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)

    # Stores password reset tokens so users can recover their account via email
    cur.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            token TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    """)

    # Stores session tokens so users stay logged in after refreshing the page
    cur.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    """)

    # The actual portfolio data — each row is one holding for one user
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_watchlists (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            ticker TEXT NOT NULL,
            amount REAL NOT NULL DEFAULT 0,
            UNIQUE(user_id, ticker)
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


# Creates a new user account, returns False if that email is already taken
def register_user(username, password, nickname=""):
    conn = get_connection()
    cur = _cur(conn)
    hashed = generate_password_hash(password)
    # Enforces the 12 character nickname limit
    _nick = (nickname or "").strip()[:12]
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, nickname) VALUES (%s, %s, %s)",
            (username, hashed, _nick),
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


# Gets the nickname for a user to show in the top right of the dashboard
def get_nickname(email: str) -> str:
    conn = get_connection()
    cur = _cur(conn)
    cur.execute("SELECT nickname FROM users WHERE username = %s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return (row["nickname"] or "").strip() if row else ""


def set_nickname(email: str, nickname: str) -> None:
    conn = get_connection()
    cur = _cur(conn)
    cur.execute(
        "UPDATE users SET nickname = %s WHERE username = %s",
        (nickname.strip()[:12], email),
    )
    conn.commit()
    cur.close()
    conn.close()


# Gets the user's role (Owner, User, etc.) to display under their name in the profile dropdown
def get_role(email: str) -> str:
    conn = get_connection()
    cur = _cur(conn)
    cur.execute("SELECT role FROM users WHERE username = %s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return (row["role"] or "User").strip() if row else "User"


def set_role(email: str, role: str) -> None:
    conn = get_connection()
    cur = _cur(conn)
    cur.execute("UPDATE users SET role = %s WHERE username = %s", (role.strip(), email))
    conn.commit()
    cur.close()
    conn.close()


# Pulls the profile picture bytes for display in the header and account dialog
def get_profile_pic(email: str) -> bytes | None:
    conn = get_connection()
    cur = _cur(conn)
    cur.execute("SELECT profile_pic FROM users WHERE username = %s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and row["profile_pic"]:
        return bytes(row["profile_pic"])
    return None


# Saves the profile picture as raw PNG bytes in the database
def set_profile_pic(email: str, png_bytes: bytes) -> None:
    conn = get_connection()
    cur = _cur(conn)
    cur.execute(
        "UPDATE users SET profile_pic = %s WHERE username = %s",
        (psycopg2.Binary(png_bytes), email),
    )
    conn.commit()
    cur.close()
    conn.close()


# Checks the password on login — handles both werkzeug and bcrypt hashed passwords
def verify_user(username, password):
    conn = get_connection()
    cur = _cur(conn)
    cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return False
    pw_hash = row["password_hash"]
    # Bcrypt hashes start with $2b$ — handled separately with the bcrypt library
    if pw_hash.startswith(("$2b$", "$2a$", "$2y$")):
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode("utf-8"), pw_hash.encode("utf-8"))
        except Exception:
            return False
    return check_password_hash(pw_hash, password)


# Saves a password reset token and cleans up any expired ones at the same time
def store_reset_token(email: str, token: str, expires_in: int = 900):
    conn = get_connection()
    cur = _cur(conn)
    cur.execute("DELETE FROM password_reset_tokens WHERE expires_at < %s", (time.time(),))
    cur.execute(
        """
        INSERT INTO password_reset_tokens (token, email, expires_at) VALUES (%s, %s, %s)
        ON CONFLICT (token) DO UPDATE SET email = EXCLUDED.email, expires_at = EXCLUDED.expires_at
        """,
        (token, email, time.time() + expires_in),
    )
    conn.commit()
    cur.close()
    conn.close()


# Returns the email tied to a reset token if it hasn't expired yet
def verify_reset_token(token: str):
    conn = get_connection()
    cur = _cur(conn)
    cur.execute(
        "SELECT email FROM password_reset_tokens WHERE token = %s AND expires_at > %s",
        (token, time.time()),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["email"] if row else None


# Deletes the reset token after it's been used so it can't be reused
def consume_reset_token(token: str):
    conn = get_connection()
    cur = _cur(conn)
    cur.execute("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
    conn.commit()
    cur.close()
    conn.close()


def update_password(email: str, new_password: str) -> bool:
    conn = get_connection()
    cur = _cur(conn)
    cur.execute(
        "UPDATE users SET password_hash = %s WHERE username = %s",
        (generate_password_hash(new_password), email),
    )
    changed = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return changed


# Not used by the main dashboard anymore but kept around just in case it's needed later
def add_asset(user_id, ticker, amount):
    conn = get_connection()
    cur = _cur(conn)
    cur.execute(
        "INSERT INTO portfolios (user_id, ticker, amount) VALUES (%s, %s, %s)",
        (user_id, ticker, amount),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_portfolio(user_id):
    conn = get_connection()
    cur = _cur(conn)
    cur.execute("SELECT ticker, amount FROM portfolios WHERE user_id = %s", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


# Generates a 30-day session token and stores it so the user stays logged in after a page refresh
def create_auth_token(email: str, expires_in: int = 30 * 24 * 3600) -> str:
    token = secrets.token_urlsafe(48)
    conn = get_connection()
    cur = _cur(conn)
    # Cleans up expired tokens in the same call to avoid letting them pile up
    cur.execute("DELETE FROM auth_tokens WHERE expires_at < %s", (time.time(),))
    cur.execute(
        "INSERT INTO auth_tokens (token, email, expires_at) VALUES (%s, %s, %s)",
        (token, email, time.time() + expires_in),
    )
    conn.commit()
    cur.close()
    conn.close()
    return token


# Checks if a session token from the cookie is still valid and returns the associated email
def verify_auth_token(token: str) -> str | None:
    conn = get_connection()
    cur = _cur(conn)
    cur.execute(
        "SELECT email FROM auth_tokens WHERE token = %s AND expires_at > %s",
        (token, time.time()),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["email"] if row else None


# Removes the session token from the database when the user explicitly logs out
def delete_auth_token(token: str) -> None:
    conn = get_connection()
    cur = _cur(conn)
    cur.execute("DELETE FROM auth_tokens WHERE token = %s", (token,))
    conn.commit()
    cur.close()
    conn.close()


# Looks up the user's integer id — needed to query the watchlist table
def get_user_id(email: str) -> int | None:
    conn = get_connection()
    cur = _cur(conn)
    cur.execute("SELECT id FROM users WHERE username = %s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["id"] if row else None


def add_to_watchlist(email: str, ticker: str, amount: float) -> bool:
    uid = get_user_id(email)
    if uid is None:
        return False
    conn = get_connection()
    cur = _cur(conn)
    try:
        cur.execute(
            "INSERT INTO user_watchlists (user_id, ticker, amount) VALUES (%s, %s, %s)",
            (uid, ticker.upper(), amount),
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


# Adds shares to an existing position or creates a new one if the ticker isn't in the portfolio yet
def upsert_watchlist(email: str, ticker: str, amount: float) -> bool:
    uid = get_user_id(email)
    if uid is None:
        return False
    conn = get_connection()
    cur = _cur(conn)
    try:
        cur.execute(
            "SELECT amount FROM user_watchlists WHERE user_id = %s AND ticker = %s",
            (uid, ticker.upper()),
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                "UPDATE user_watchlists SET amount = amount + %s WHERE user_id = %s AND ticker = %s",
                (amount, uid, ticker.upper()),
            )
        else:
            cur.execute(
                "INSERT INTO user_watchlists (user_id, ticker, amount) VALUES (%s, %s, %s)",
                (uid, ticker.upper(), amount),
            )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# Returns the user's full portfolio as a list of dicts with ticker and quantity
def get_watchlist(email: str) -> list:
    uid = get_user_id(email)
    if uid is None:
        return []
    conn = get_connection()
    cur = _cur(conn)
    cur.execute(
        "SELECT ticker, amount FROM user_watchlists WHERE user_id = %s ORDER BY id",
        (uid,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"ticker": r["ticker"], "amount": r["amount"]} for r in rows]


def remove_from_watchlist(email: str, ticker: str) -> None:
    uid = get_user_id(email)
    if uid is None:
        return
    conn = get_connection()
    cur = _cur(conn)
    cur.execute(
        "DELETE FROM user_watchlists WHERE user_id = %s AND ticker = %s",
        (uid, ticker.upper()),
    )
    conn.commit()
    cur.close()
    conn.close()


# Replaces the entire portfolio at once — used by the manage portfolio dialog when saving changes
def set_watchlist(email: str, entries: list) -> None:
    uid = get_user_id(email)
    if uid is None:
        return
    conn = get_connection()
    cur = _cur(conn)
    try:
        # Wipes everything first then reinserts the updated list
        cur.execute("DELETE FROM user_watchlists WHERE user_id = %s", (uid,))
        for e in entries:
            ticker = str(e.get("ticker", "") or "").upper().strip()
            try:
                amount = float(e.get("amount", 0) or 0)
            except (ValueError, TypeError):
                amount = 0.0
            if ticker and amount > 0:
                cur.execute(
                    "INSERT INTO user_watchlists (user_id, ticker, amount) VALUES (%s, %s, %s)",
                    (uid, ticker, amount),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
