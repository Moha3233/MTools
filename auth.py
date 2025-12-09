# auth.py
import sqlite3
import bcrypt
from pathlib import Path

DB_NAME = "users.db"

def init_user_db(db_path: str = DB_NAME):
    """Ensure DB exists and has users table."""
    path = Path(db_path)
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password BLOB
        )
    """)
    conn.commit()
    conn.close()

def add_user(username: str, password: str, db_path: str = DB_NAME) -> bool:
    """Add a new user. Returns True if created, False if username exists."""
    if not username or not password:
        return False
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def validate_user(username: str, password: str, db_path: str = DB_NAME) -> bool:
    """Validate credentials. Returns True if valid."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username=?", (username,))
    result = cur.fetchone()
    conn.close()
    if result:
        hashed = result[0]
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed)
        except Exception:
            return False
    return False
