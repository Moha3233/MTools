# auth.py
import sqlite3
from passlib.hash import bcrypt
from pathlib import Path

DB_NAME = "users.db"

def init_user_db(db_path: str = DB_NAME):
    path = Path(db_path)
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(username: str, password: str, db_path: str = DB_NAME) -> bool:
    if not username or not password:
        return False
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    hashed = bcrypt.hash(password)
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def validate_user(username: str, password: str, db_path: str = DB_NAME) -> bool:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username=?", (username,))
    result = cur.fetchone()
    conn.close()
    if result:
        stored_hash = result[0]
        return bcrypt.verify(password, stored_hash)
    return False
