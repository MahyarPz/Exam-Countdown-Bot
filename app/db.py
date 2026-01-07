"""Database operations for users and exams."""

import logging
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from app.config import Config

logger = logging.getLogger(__name__)

# Try to import psycopg2 for PostgreSQL support
try:  # pragma: no cover - optional dependency
    import psycopg2
    from psycopg2.extras import RealDictCursor

    POSTGRES_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    POSTGRES_AVAILABLE = False
    logger.warning("psycopg2 not installed. PostgreSQL support disabled.")


@contextmanager
def get_db():
    """Context manager yielding a DB connection and handling commit/close."""
    if Config.use_postgres():
        if not POSTGRES_AVAILABLE:
            raise RuntimeError("PostgreSQL URL provided but psycopg2 not installed")
        conn = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    timezone VARCHAR(100) NOT NULL DEFAULT 'Europe/Rome',
                    notify_time VARCHAR(5) NOT NULL DEFAULT '09:00'
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS exams (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    title TEXT NOT NULL,
                    exam_datetime_iso TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """
            )
            logger.info("PostgreSQL database initialized successfully")
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    timezone TEXT NOT NULL DEFAULT 'Europe/Rome',
                    notify_time TEXT NOT NULL DEFAULT '09:00'
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    exam_datetime_iso TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                """
            )
            logger.info("SQLite database initialized successfully")


def _dict_row(row: Any) -> Dict[str, Any]:
    """Convert a DB row to a plain dict."""
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    return dict(row)


def get_or_create_user(user_id: int) -> Dict[str, Any]:
    """Return user row; create with defaults if missing."""
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                cursor.execute(
                    "INSERT INTO users (user_id, timezone, notify_time) VALUES (%s, %s, %s)",
                    (user_id, Config.DEFAULT_TIMEZONE, Config.DEFAULT_NOTIFY_TIME),
                )
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()
        else:
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                cursor.execute(
                    "INSERT INTO users (user_id, timezone, notify_time) VALUES (?, ?, ?)",
                    (user_id, Config.DEFAULT_TIMEZONE, Config.DEFAULT_NOTIFY_TIME),
                )
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user = cursor.fetchone()
        return _dict_row(user)


def update_user_timezone(user_id: int, timezone: str) -> None:
    """Update user's timezone."""
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "UPDATE users SET timezone = %s WHERE user_id = %s",
                (timezone, user_id),
            )
        else:
            cursor.execute(
                "UPDATE users SET timezone = ? WHERE user_id = ?",
                (timezone, user_id),
            )


def update_user_notify_time(user_id: int, notify_time: str) -> None:
    """Update user's notification time."""
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "UPDATE users SET notify_time = %s WHERE user_id = %s",
                (notify_time, user_id),
            )
        else:
            cursor.execute(
                "UPDATE users SET notify_time = ? WHERE user_id = ?",
                (notify_time, user_id),
            )


def add_exam(user_id: int, title: str, exam_datetime_iso: str) -> int:
    """Insert a new exam and return its id."""
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "INSERT INTO exams (user_id, title, exam_datetime_iso) VALUES (%s, %s, %s) RETURNING id",
                (user_id, title, exam_datetime_iso),
            )
            row = cursor.fetchone()
            return int(row["id"] if isinstance(row, dict) else row[0])
        cursor.execute(
            "INSERT INTO exams (user_id, title, exam_datetime_iso) VALUES (?, ?, ?)",
            (user_id, title, exam_datetime_iso),
        )
        return int(cursor.lastrowid)


def get_user_exams(user_id: int) -> List[Dict[str, Any]]:
    """Return all exams for a user ordered by datetime."""
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "SELECT * FROM exams WHERE user_id = %s ORDER BY exam_datetime_iso",
                (user_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM exams WHERE user_id = ? ORDER BY exam_datetime_iso",
                (user_id,),
            )
        return [_dict_row(row) for row in cursor.fetchall()]


def delete_exam(exam_id: int, user_id: int) -> bool:
    """Delete an exam (only if it belongs to the user)."""
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "DELETE FROM exams WHERE id = %s AND user_id = %s",
                (exam_id, user_id),
            )
        else:
            cursor.execute(
                "DELETE FROM exams WHERE id = ? AND user_id = ?",
                (exam_id, user_id),
            )
        return cursor.rowcount > 0


def get_exam_by_id(exam_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific exam by ID (only if it belongs to the user)."""
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "SELECT * FROM exams WHERE id = %s AND user_id = %s",
                (exam_id, user_id),
            )
        else:
            cursor.execute(
                "SELECT * FROM exams WHERE id = ? AND user_id = ?",
                (exam_id, user_id),
            )
        row = cursor.fetchone()
        return _dict_row(row) if row else None
