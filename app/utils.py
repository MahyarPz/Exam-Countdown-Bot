"""Utility functions for date parsing and formatting."""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import pytz
import re


def parse_exam_datetime(date_str: str, default_time: str = "09:00") -> Optional[str]:
    """
    Parse exam date/time string and return ISO format.
    
    Supports:
    - YYYY-MM-DD (defaults to 09:00)
    - YYYY-MM-DD HH:MM
    
    Returns ISO format string or None if invalid.
    """
    date_str = date_str.strip()
    
    # Try YYYY-MM-DD HH:MM format
    pattern_with_time = r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})'
    match = re.match(pattern_with_time, date_str)
    if match:
        try:
            dt = datetime(
                int(match.group(1)),  # year
                int(match.group(2)),  # month
                int(match.group(3)),  # day
                int(match.group(4)),  # hour
                int(match.group(5))   # minute
            )
            return dt.isoformat()
        except ValueError:
            return None
    
    # Try YYYY-MM-DD format (add default time)
    pattern_date_only = r'(\d{4})-(\d{2})-(\d{2})$'
    match = re.match(pattern_date_only, date_str)
    if match:
        try:
            hour, minute = map(int, default_time.split(':'))
            dt = datetime(
                int(match.group(1)),  # year
                int(match.group(2)),  # month
                int(match.group(3)),  # day
                hour,
                minute
            )
            return dt.isoformat()
        except ValueError:
            return None
    
    return None


def parse_time(time_str: str) -> Optional[str]:
    """
    Parse time string in HH:MM format.
    Returns normalized HH:MM string or None if invalid.
    """
    time_str = time_str.strip()
    pattern = r'^(\d{1,2}):(\d{2})$'
    match = re.match(pattern, time_str)
    
    if match:
        try:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour < 24 and 0 <= minute < 60:
                return f"{hour:02d}:{minute:02d}"
        except ValueError:
            pass
    
    return None


def validate_timezone(tz_str: str) -> bool:
    """Check if timezone string is valid IANA timezone."""
    try:
        pytz.timezone(tz_str)
        return True
    except pytz.exceptions.UnknownTimeZoneError:
        return False


def format_exam_countdown(exam_datetime_iso: str, user_timezone: str) -> Tuple[str, int]:
    """
    Calculate days until exam and format countdown message.
    
    Returns:
        Tuple of (formatted_message, days_until)
        e.g., ("5 days left", 5) or ("today", 0) or ("tomorrow", 1)
    """
    exam_dt = datetime.fromisoformat(exam_datetime_iso)
    
    # Get current time in user's timezone
    tz = pytz.timezone(user_timezone)
    now = datetime.now(tz).replace(tzinfo=None)
    
    # Calculate difference based on DATE only, not time
    # This fixes the issue where an exam later today shows as "passed"
    exam_date = exam_dt.date()
    today_date = now.date()
    days = (exam_date - today_date).days
    
    if days < 0:
        return "passed", days
    elif days == 0:
        return "today", 0
    elif days == 1:
        return "tomorrow", 1
    else:
        return f"{days} days left", days


def get_upcoming_exams_message(exams: list, user_timezone: str) -> Optional[str]:
    """
    Generate daily notification message for upcoming exams.
    Returns None if no upcoming exams.
    """
    if not exams:
        return None
    
    upcoming = []
    for exam in exams:
        countdown_msg, days = format_exam_countdown(
            exam['exam_datetime_iso'],
            user_timezone
        )
        # Only include future exams or today
        if days >= 0:
            upcoming.append(f"- {exam['title']} — {countdown_msg}")
    
    if not upcoming:
        return None
    
    return "📚 Exam reminder:\n" + "\n".join(upcoming)
