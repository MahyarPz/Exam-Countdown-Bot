"""Database operations for users and exams."""

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from app.config import Config

logger = logging.getLogger(__name__)

# Try to import psycopg2 for PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logger.warning("psycopg2 not installed. PostgreSQL support disabled.")


@contextmanager
def get_db():
    """Context manager for database connections."""
    if Config.use_postgres():
        if not POSTGRES_AVAILABLE:
            raise RuntimeError("PostgreSQL URL provided but psycopg2 not installed")
        
        # PostgreSQL connection
        conn = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
        try:
            yield conn
            conn.commit()
        if Config.use_postgres():
            # PostgreSQL syntax
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    timezone VARCHAR(100) NOT NULL DEFAULT 'Europe/Rome',
                    notify_time VARCHAR(5) NOT NULL DEFAULT '09:00'
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exams (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    title TEXT NOT NULL,
                    exam_datetime_iso TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            logger.info("PostgreSQL database initialized successfully")
        else:
            # SQLite syntax
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    timezone TEXT NOT NULL DEFAULT 'Europe/Rome',
                    notify_time TEXT NOT NULL DEFAULT '09:00'
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    exam_datetime_iso TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            logger.info("SQLite d
def init_db() -> None:
    """Initialize database tables."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                timezone TEXT NOT NULL DEFAULT 'Europe/Rome',
                notify_time TEXT NOT NULL DEFAULT '09:00'
            )
        """)
        
        # Exams table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                exam_datetime_iso TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        logger.info("Database initialized successfully")


# User operations
def get_or_create_user(user_id: int) -> Dict[str, Any]:
    """Get user or create if doesn't exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if Config.use_postgres():
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.execute(
                    "INSERT INTO users (user_id, timezone, notify_time) VALUES (%s, %s, %s)",
                    (user_id, Config.DEFAULT_TIMEZONE, Config.DEFAULT_NOTIFY_TIME)
                )
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()
        else:
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.execute(
        if Config.use_postgres():
            cursor.execute(
                "UPDATE users SET timezone = %s WHERE user_id = %s",
                (timezone, user_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET timezone = ? WHERE user_id = ?",
                (timezone, user_id)
            )


def update_user_notify_time(user_id: int, notify_time: str) -> None:
    """Update user's notification time."""
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "UPDATE users SET notify_time = %s WHERE user_id = %s",
                (notify_time, user_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET notify_time = ? WHERE user_id = ?",
                (notify_time, user_id)
            cursor.execute(
            "UPDATE users SET timezone = ? WHERE user_id = ?",
            (timezone, user_id)
        )


def update_user_notify_time(user_id: int, notify_time: str) -> None:
    """Update user's notification time."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if Config.use_postgres():
            cursor.execute(
                "INSERT INTO exams (user_id, title, exam_datetime_iso) VALUES (%s, %s, %s) RETURNING id",
                (user_id, title, exam_datetime_iso)
            )
            return cursor.fetchone()['id']
        else:
            cursor.execute(
                "INSERT INTO exams (user_id, title, exam_datetime_iso) VALUES (?, ?, ?)",
                (user_id, title, exam_datetime_iso)
            )
    
if Config.use_postgres():
            cursor.execute(
                "SELECT * FROM exams WHERE user_id = %s ORDER BY exam_datetime_iso",
                (user_id,)
            )
        else:
            cursor.execute(
                "SELECT * FROM exams WHERE user_id = ? ORDER BY exam_datetime_iso",
                (user_id,)
            )
        return [dict(row) for row in cursor.fetchall()]


def delete_exam(exam_id: int, user_id: int) -> bool:
    """Delete an exam (only if it belongs to the user)."""
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "DELETE FROM exams WHERE id = %s AND user_id = %s",
                (exam_id, user_id)
            )
        else:
            cursor.execute(
                "DELETE FROM exams WHERE id = ? AND user_id = ?",
                (exam_id, user_id)
            )
        return cursor.rowcount > 0


def get_exam_by_id(exam_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific exam by ID (only if it belongs to the user)."""
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "SELECT * FROM exams WHERE id = %s AND user_id = %s",
                (exam_id, user_id)
            )
        else:
            cursor.execute(
                "SELECT * FROM exams WHERE id = ? AND user_id = ?",
                (exam_id, user_id)
            cursor.execute(
            "SELECT * FROM exams WHERE user_id = ? ORDER BY exam_datetime_iso",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def delete_exam(exam_id: int, user_id: int) -> bool:
    """Delete an exam (only if it belongs to the user)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM exams WHERE id = ? AND user_id = ?",
            (exam_id, user_id)
        )
        return cursor.rowcount > 0


def get_exam_by_id(exam_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific exam by ID (only if it belongs to the user)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM exams WHERE id = ? AND user_id = ?",
            (exam_id, user_id)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
