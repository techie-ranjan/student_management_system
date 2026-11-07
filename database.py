"""SQLite helpers for the Student Management System."""
import os
import sqlite3

DB_PATH = os.environ.get(
    "SMS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")
)

SUBJECTS = ["python", "dbms", "maths", "web", "english"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no    TEXT    NOT NULL UNIQUE,
    name       TEXT    NOT NULL,
    email      TEXT    NOT NULL DEFAULT '',
    course     TEXT    NOT NULL DEFAULT 'BCA',
    semester   INTEGER NOT NULL DEFAULT 1,
    python     REAL    NOT NULL DEFAULT 0,
    dbms       REAL    NOT NULL DEFAULT 0,
    maths      REAL    NOT NULL DEFAULT 0,
    web        REAL    NOT NULL DEFAULT 0,
    english    REAL    NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def get_conn():
    """Open a connection (reads DB_PATH at call time so tests can override it)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
