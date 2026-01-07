"""Scheduler for daily exam reminders."""

import logging
from datetime import time
from telegram.ext import ContextTypes, Application
import pytz
from app import db
from app.utils import get_upcoming_exams_message
from app.config import Config

logger = logging.getLogger(__name__)


async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send daily reminder to a user."""
    user_id = context.job.data
    
    try:
        # Get user info
        user = db.get_or_create_user(user_id)
        
        # Get user's exams
        exams = db.get_user_exams(user_id)
        
        # Generate message
        message = get_upcoming_exams_message(exams, user['timezone'])
        
        if message:
            await context.bot.send_message(
                chat_id=user_id,
                text=message
            )
            logger.info(f"Sent daily reminder to user {user_id}")
        else:
            logger.debug(f"No upcoming exams for user {user_id}, skipping reminder")
    
    except Exception as e:
        logger.error(f"Error sending daily reminder to user {user_id}: {e}")


def schedule_user_reminder(application: Application, user_id: int, notify_time_str: str, timezone_str: str) -> None:
    """
    Schedule or reschedule daily reminder for a user.
    
    Args:
        application: The Application instance
        user_id: User's Telegram ID
        notify_time_str: Time in HH:MM format
        timezone_str: IANA timezone string
    """
    job_name = f"daily:{user_id}"

    job_queue = application.job_queue
    if job_queue is None:
        logger.error("Job queue is not available; skipping scheduling for user %s", user_id)
        return
    
    # Remove existing job if present
    current_jobs = job_queue.get_jobs_by_name(job_name)
    for job in current_jobs:
        job.schedule_removal()
    
    # Parse time
    hour, minute = map(int, notify_time_str.split(':'))
    notify_time = time(hour=hour, minute=minute)
    
    # Get timezone
    tz = pytz.timezone(timezone_str)
    
    # Schedule job
    if Config.DEBUG_FAST_SCHEDULE:
        # For testing: run every 60 seconds
        job_queue.run_repeating(
            send_daily_reminder,
            interval=60,
            first=5,  # Start after 5 seconds
            data=user_id,
            name=job_name
        )
        logger.info(f"Scheduled FAST reminder for user {user_id} every 60 seconds")
    else:
        # Normal: run daily at specified time
        job_queue.run_daily(
            send_daily_reminder,
            time=notify_time,
            days=(0, 1, 2, 3, 4, 5, 6),  # All days
            data=user_id,
            name=job_name,
            chat_id=user_id,
            tzinfo=tz
        )
        logger.info(f"Scheduled daily reminder for user {user_id} at {notify_time_str} {timezone_str}")


def reschedule_user_reminder(application: Application, user_id: int) -> None:
    """Reschedule reminder for a user (re-read from DB)."""
    user = db.get_or_create_user(user_id)
    schedule_user_reminder(
        application,
        user_id,
        user['notify_time'],
        user['timezone']
    )


def schedule_all_users(application: Application) -> None:
    """Schedule reminders for all users in the database."""
    users = db.get_all_users()
    for user in users:
        schedule_user_reminder(
            application,
            user['user_id'],
            user['notify_time'],
            user['timezone']
        )
    logger.info(f"Scheduled reminders for {len(users)} users")
