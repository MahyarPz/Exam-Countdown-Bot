"""Database operations for users and exams - supports SQLite, PostgreSQL, and Firestore."""

import logging
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from app.config import Config

logger = logging.getLogger(__name__)

# Import Firestore module if using Firestore
if Config.use_firestore():
    from app import firestore_db
    _firestore_initialized = False
else:
    firestore_db = None
    _firestore_initialized = False

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
    """Initialize database (SQLite, PostgreSQL, or Firestore)."""
    global _firestore_initialized
    
    if Config.use_firestore():
        try:
            firestore_db.init_firestore()
            _firestore_initialized = True
            logger.info("Using Firestore database")
        except Exception as e:
            logger.error(f"Firestore initialization failed: {e}")
            raise
    else:
        # Existing SQLite/PostgreSQL initialization
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
                        user_exam_id INTEGER,
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
                        user_exam_id INTEGER,
                        title TEXT NOT NULL,
                        exam_datetime_iso TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                    """
                )
                logger.info("SQLite database initialized successfully")

            try:
                _ensure_user_exam_id(conn, cursor)
            except Exception as e:
                logger.error(f"Error in _ensure_user_exam_id: {e}. Continuing anyway.")
                conn.rollback()


def _dict_row(row: Any) -> Dict[str, Any]:
    """Convert a DB row to a plain dict."""
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    return dict(row)


def _has_column(cursor: Any, table_name: str, column_name: str) -> bool:
    """Return True if a column exists in the given table."""
    if Config.use_postgres():
        cursor.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s",
            (table_name, column_name),
        )
        return cursor.fetchone() is not None

    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())


def _ensure_user_exam_id(conn: Any, cursor: Any) -> None:
    """Ensure per-user exam IDs exist and are populated."""
    try:
        # Check if column exists
        if not _has_column(cursor, "exams", "user_exam_id"):
            logger.info("Adding user_exam_id column to exams table...")
            if Config.use_postgres():
                cursor.execute("ALTER TABLE exams ADD COLUMN user_exam_id INTEGER")
            else:
                cursor.execute("ALTER TABLE exams ADD COLUMN user_exam_id INTEGER")
            conn.commit()
    
        # Backfill missing user_exam_id values
        _backfill_user_exam_id(cursor)
    
        # Create index if it doesn't exist
        try:
            if Config.use_postgres():
                cursor.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_exams_user_exam_per_user ON exams(user_id, user_exam_id)"
                )
            else:
                cursor.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_exams_user_exam_per_user ON exams(user_id, user_exam_id)"
                )
        except Exception as e:
            logger.debug(f"Index creation failed (might already exist): {e}")
        
        conn.commit()
        logger.info("user_exam_id migration completed successfully")
    
    except Exception as e:
        logger.error(f"Error in _ensure_user_exam_id: {e}")
        conn.rollback()
        raise


def _backfill_user_exam_id(cursor: Any) -> None:
    """Assign sequential user_exam_id per user for existing rows."""
    try:
        if Config.use_postgres():
            cursor.execute("SELECT DISTINCT user_id FROM exams WHERE user_exam_id IS NULL")
        else:
            cursor.execute("SELECT DISTINCT user_id FROM exams WHERE user_exam_id IS NULL")
        
        users_missing = cursor.fetchall()
        
        if not users_missing:
            logger.debug("No exams need user_exam_id backfill")
            return
        
        logger.info(f"Backfilling user_exam_id for {len(users_missing)} users...")

        for row in users_missing:
            user_id = row[0] if not isinstance(row, dict) else row.get("user_id")
            if user_id is None:
                continue
            
            if Config.use_postgres():
                cursor.execute(
                    "SELECT id FROM exams WHERE user_id = %s AND user_exam_id IS NULL ORDER BY id",
                    (user_id,),
                )
            else:
                cursor.execute(
                    "SELECT id FROM exams WHERE user_id = ? AND user_exam_id IS NULL ORDER BY id",
                    (user_id,),
                )
            
            rows = cursor.fetchall()
            for idx, exam_row in enumerate(rows, start=1):
                exam_id = exam_row[0] if not isinstance(exam_row, dict) else exam_row.get("id")
                if exam_id is None:
                    continue
                
                if Config.use_postgres():
                    cursor.execute(
                        "UPDATE exams SET user_exam_id = %s WHERE id = %s",
                        (idx, exam_id),
                    )
                else:
                    cursor.execute(
                        "UPDATE exams SET user_exam_id = ? WHERE id = ?",
                        (idx, exam_id),
                    )
        
        logger.info("Backfill completed successfully")
    
    except Exception as e:
        logger.error(f"Error in _backfill_user_exam_id: {e}")
        raise


def _next_user_exam_id(cursor: Any, user_id: int) -> int:
    """Return next sequential exam id for the user."""
    if Config.use_postgres():
        cursor.execute("SELECT COALESCE(MAX(user_exam_id), 0) + 1 FROM exams WHERE user_id = %s", (user_id,))
    else:
        cursor.execute("SELECT COALESCE(MAX(user_exam_id), 0) + 1 FROM exams WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return int(row[0] if not isinstance(row, dict) else list(row.values())[0])


def get_or_create_user(user_id: int) -> Dict[str, Any]:
    """Return user row; create with defaults if missing."""
    if Config.use_firestore():
        return firestore_db.get_or_create_user(user_id)
    
    # Existing SQLite/PostgreSQL code
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
    if Config.use_firestore():
        firestore_db.update_user_timezone(user_id, timezone)
    else:
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
    if Config.use_firestore():
        firestore_db.update_user_notify_time(user_id, notify_time)
    else:
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
    """Insert a new exam and return its per-user id."""
    if Config.use_firestore():
        return firestore_db.add_exam(user_id, title, exam_datetime_iso)
    
    # Existing SQLite/PostgreSQL code
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            _ensure_user_exam_id(conn, cursor)
        except Exception as e:
            logger.warning(f"Migration warning: {e}")

        user_exam_id = _next_user_exam_id(cursor, user_id)

        if Config.use_postgres():
            cursor.execute(
                "INSERT INTO exams (user_id, user_exam_id, title, exam_datetime_iso) VALUES (%s, %s, %s, %s) RETURNING user_exam_id",
                (user_id, user_exam_id, title, exam_datetime_iso),
            )
            row = cursor.fetchone()
            return int(row["user_exam_id"] if isinstance(row, dict) else row[0])
        cursor.execute(
            "INSERT INTO exams (user_id, user_exam_id, title, exam_datetime_iso) VALUES (?, ?, ?, ?)",
            (user_id, user_exam_id, title, exam_datetime_iso),
        )
        return int(user_exam_id)


def get_user_exams(user_id: int) -> List[Dict[str, Any]]:
    """Return all exams for a user ordered by datetime."""
    if Config.use_firestore():
        return firestore_db.get_user_exams(user_id)
    
    # Existing SQLite/PostgreSQL code
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "SELECT * FROM exams WHERE user_id = %s ORDER BY user_exam_id",
                (user_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM exams WHERE user_id = ? ORDER BY user_exam_id",
                (user_id,),
            )
        return [_dict_row(row) for row in cursor.fetchall()]


def get_all_users() -> List[Dict[str, Any]]:
    """Return all users."""
    if Config.use_firestore():
        return firestore_db.get_all_users()
    
    # Existing SQLite/PostgreSQL code
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute("SELECT * FROM users ORDER BY user_id")
        else:
            cursor.execute("SELECT * FROM users ORDER BY user_id")
        return [_dict_row(row) for row in cursor.fetchall()]


def delete_exam(user_exam_id: int, user_id: int) -> bool:
    """Delete an exam (only if it belongs to the user)."""
    if Config.use_firestore():
        return firestore_db.delete_exam(user_exam_id, user_id)
    
    # Existing SQLite/PostgreSQL code
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "DELETE FROM exams WHERE user_exam_id = %s AND user_id = %s",
                (user_exam_id, user_id),
            )
        else:
            cursor.execute(
                "DELETE FROM exams WHERE user_exam_id = ? AND user_id = ?",
                (user_exam_id, user_id),
            )
        return cursor.rowcount > 0


def get_exam_by_id(user_exam_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific exam by per-user ID (only if it belongs to the user)."""
    if Config.use_firestore():
        return firestore_db.get_exam_by_id(user_exam_id, user_id)
    
    # Existing SQLite/PostgreSQL code
    with get_db() as conn:
        cursor = conn.cursor()
        if Config.use_postgres():
            cursor.execute(
                "SELECT * FROM exams WHERE user_exam_id = %s AND user_id = %s",
                (user_exam_id, user_id),
            )
        else:
            cursor.execute(
                "SELECT * FROM exams WHERE user_exam_id = ? AND user_id = ?",
                (user_exam_id, user_id),
            )
        row = cursor.fetchone()
        return _dict_row(row) if row else None
