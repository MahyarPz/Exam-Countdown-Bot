"""Command and callback handlers."""

import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from app import db
from app.config import Config
from app.utils import (
    parse_exam_datetime,
    parse_time,
    validate_timezone,
    format_exam_countdown,
    get_upcoming_exams_message
)
from app.keyboards import get_main_menu_keyboard, get_exam_list_inline_keyboard
from app.scheduler import reschedule_user_reminder, ensure_user_scheduled

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user_id = update.effective_user.id
    user = db.get_or_create_user(user_id)
    
    # Schedule daily reminder for this user
    reschedule_user_reminder(context.application, user_id)
    
    welcome_text = (
        f"👋 Welcome to Exam Countdown Bot!\n\n"
        f"I'll help you track your exams and send daily reminders.\n\n"
        f"Use the menu buttons below to get started! 👇"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )
    logger.info(f"User {user_id} started the bot")


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu command - show the main menu keyboard."""
    await update.message.reply_text(
        "📱 Here's your menu:",
        reply_markup=get_main_menu_keyboard()
    )


async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /debug command - show scheduler status."""
    user_id = update.effective_user.id
    user = db.get_or_create_user(user_id)
    
    # Get job queue info
    job_queue = context.application.job_queue
    job_name = f"daily:{user_id}"
    jobs = job_queue.get_jobs_by_name(job_name) if job_queue else []
    
    lines = [
        "🔧 **Debug Info:**\n",
        f"👤 User ID: `{user_id}`",
        f"🌍 Timezone: `{user['timezone']}`",
        f"⏰ Notify Time: `{user['notify_time']}`",
        f"🕐 Server Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        f"\n📋 **Scheduled Jobs:** {len(jobs)}",
    ]
    
    for job in jobs:
        try:
            next_run = getattr(job, 'next_t', None) or getattr(job.job, 'next_run_time', None)
            next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S %Z') if next_run else 'N/A'
        except Exception:
            next_run_str = 'N/A'
        lines.append(f"  • Job: `{job.name}`")
        lines.append(f"    Next run: `{next_run_str}`")
    
    if not jobs:
        lines.append("  ⚠️ No jobs scheduled for you!")
        lines.append("  Use /schedule to create one")
    
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode='Markdown'
    )


async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /schedule command - force create a scheduled job."""
    user_id = update.effective_user.id
    user = db.get_or_create_user(user_id)
    
    # Force reschedule
    try:
        reschedule_user_reminder(context.application, user_id)
        
        # Verify it was created
        job_queue = context.application.job_queue
        job_name = f"daily:{user_id}"
        jobs = job_queue.get_jobs_by_name(job_name) if job_queue else []
        
        if jobs:
            job = jobs[0]
            try:
                next_run = getattr(job, 'next_t', None) or getattr(job.job, 'next_run_time', None)
                next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S %Z') if next_run else 'Scheduled'
            except Exception:
                next_run_str = 'Scheduled'
            await update.message.reply_text(
                f"✅ **Notification scheduled!**\n\n"
                f"⏰ Time: `{user['notify_time']}`\n"
                f"🌍 Timezone: `{user['timezone']}`\n"
                f"📅 Next run: `{next_run_str}`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Failed to create job. Job queue might not be available."
            )
    except Exception as e:
        logger.error(f"Error scheduling for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error: {str(e)}"
        )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command and Help button."""
    help_text = (
        "ℹ️ **Exam Countdown Bot Help**\n\n"
        "**Menu Buttons:**\n"
        "• ➕ Add Exam - Add a new exam with title and date\n"
        "• 📋 List Exams - View all your exams\n"
        "• 🗑 Delete Exam - Remove an exam\n"
        "• ⏰ Set Daily Time - Change notification time (HH:MM)\n"
        "• 🌍 Set Timezone - Set your timezone (e.g., Europe/Rome)\n"
        "• ℹ️ Help - Show this message\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/menu - Show menu keyboard\n"
        "/add <title> | <date> - Quick add exam\n"
        "/list - List all exams\n"
        "/delete <id> - Delete exam by ID\n"
        "/settime <HH:MM> - Set notification time\n"
        "/timezone <tz> - Set timezone\n"
        "/help - Show help\n\n"
        "**Date Formats:**\n"
        "• YYYY-MM-DD (defaults to 09:00)\n"
        "• YYYY-MM-DD HH:MM\n\n"
        "Example: 2026-01-15 14:30"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown'
    )


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /add command with arguments."""
    user_id = update.effective_user.id
    db.get_or_create_user(user_id)
    
    # Parse arguments
    if not context.args:
        await update.message.reply_text(
            "⚠️ Usage: /add <title> | <date>\n\n"
            "Example: /add Math Final | 2026-01-15 14:00\n\n"
            "Or use the ➕ Add Exam button for guided input."
        )
        return
    
    full_text = ' '.join(context.args)
    
    if '|' not in full_text:
        await update.message.reply_text(
            "⚠️ Please separate title and date with | (pipe)\n\n"
            "Example: /add Math Final | 2026-01-15 14:00"
        )
        return
    
    parts = full_text.split('|', 1)
    title = parts[0].strip()
    date_str = parts[1].strip()
    
    if not title:
        await update.message.reply_text("⚠️ Title cannot be empty!")
        return
    
    # Parse datetime
    exam_datetime_iso = parse_exam_datetime(date_str)
    if not exam_datetime_iso:
        await update.message.reply_text(
            "⚠️ Invalid date format!\n\n"
            "Use:\n"
            "• YYYY-MM-DD (e.g., 2026-01-15)\n"
            "• YYYY-MM-DD HH:MM (e.g., 2026-01-15 14:30)"
        )
        return
    
    # Save to database
        exam_id = db.add_exam(user_id, title, exam_datetime_iso)
    
    await update.message.reply_text(
        f"✅ Exam added successfully!\n\n"
        f"📚 {title}\n"
        f"📅 {exam_datetime_iso.replace('T', ' ')}\n"
            f"🆔 ID: {exam_id}"
    )
    
    logger.info(f"User {user_id} added exam via command: {title}")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list command and List Exams button."""
    user_id = update.effective_user.id
    user = db.get_or_create_user(user_id)
    exams = db.get_user_exams(user_id)
    
    # Ensure user has a scheduled job (in case Heroku dyno restarted)
    ensure_user_scheduled(context.application, user_id)
    
    if not exams:
        await update.message.reply_text(
            "📋 You have no exams yet.\n\n"
            "Use ➕ Add Exam to add your first exam!"
        )
        return
    
    # Build message
    lines = ["📋 **Your Exams:**\n"]
    for exam in exams:
        countdown_msg, days = format_exam_countdown(
            exam['exam_datetime_iso'],
            user['timezone']
        )
        lines.append(
            f"🆔 {exam['user_exam_id']}: **{exam['title']}**\n"
            f"   📅 {exam['exam_datetime_iso'].replace('T', ' ')}\n"
            f"   ⏳ {countdown_msg}\n"
        )
    
    message_text = '\n'.join(lines)
    
    # Add inline keyboard
    keyboard = get_exam_list_inline_keyboard(exams, show_delete_buttons=False)
    
    await update.message.reply_text(
        message_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )


async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /delete command."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "⚠️ Usage: /delete <exam_id>\n\n"
            "Example: /delete 1\n\n"
            "Use /list to see exam IDs or tap 🗑 Delete Exam button."
        )
        return
    
    try:
        exam_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Exam ID must be a number!")
        return
    
    # Delete exam
    success = db.delete_exam(exam_id, user_id)
    
    if success:
        await update.message.reply_text(f"✅ Exam #{exam_id} deleted successfully!")
        logger.info(f"User {user_id} deleted exam {exam_id}")
    else:
        await update.message.reply_text(
            f"⚠️ Exam #{exam_id} not found or doesn't belong to you."
        )


async def btn_delete_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Delete Exam button - show list with delete buttons."""
    user_id = update.effective_user.id
    user = db.get_or_create_user(user_id)
    exams = db.get_user_exams(user_id)
    
    if not exams:
        await update.message.reply_text(
            "📋 You have no exams to delete.\n\n"
            "Use ➕ Add Exam to add your first exam!"
        )
        return
    
    # Build message
    lines = ["🗑 **Select exam to delete:**\n"]
    for exam in exams[:10]:  # Show first 10
        countdown_msg, _ = format_exam_countdown(
            exam['exam_datetime_iso'],
            user['timezone']
        )
        lines.append(
            f"🆔 {exam['user_exam_id']}: {exam['title']}\n"
            f"   📅 {exam['exam_datetime_iso'].replace('T', ' ')}\n"
            f"   ⏳ {countdown_msg}\n"
        )
    
    message_text = '\n'.join(lines)
    
    # Add inline keyboard with delete buttons
    keyboard = get_exam_list_inline_keyboard(exams, show_delete_buttons=True)
    
    await update.message.reply_text(
        message_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )


async def cmd_settime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settime command and Set Daily Time button."""
    user_id = update.effective_user.id
    db.get_or_create_user(user_id)
    
    if not context.args:
        await update.message.reply_text(
            "⏰ **Set Daily Notification Time**\n\n"
            "Usage: /settime <HH:MM>\n\n"
            "Example: /settime 09:00\n\n"
            "Or just send the time in HH:MM format."
        )
        return
    
    time_str = context.args[0]
    normalized_time = parse_time(time_str)
    
    if not normalized_time:
        await update.message.reply_text(
            "⚠️ Invalid time format!\n\n"
            "Use HH:MM format (e.g., 09:00 or 14:30)"
        )
        return
    
    # Update in database
    db.update_user_notify_time(user_id, normalized_time)
    
    # Reschedule reminder
    reschedule_user_reminder(context.application, user_id)
    
    await update.message.reply_text(
        f"✅ Daily notification time set to {normalized_time}!"
    )
    
    logger.info(f"User {user_id} set notification time to {normalized_time}")


async def btn_set_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Set Daily Time button."""
    await update.message.reply_text(
        "⏰ **Set Daily Notification Time**\n\n"
        "Please send your preferred time in HH:MM format.\n\n"
        "Example: 09:00 or 14:30"
    )


async def cmd_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /timezone command and Set Timezone button."""
    user_id = update.effective_user.id
    db.get_or_create_user(user_id)
    
    if not context.args:
        await update.message.reply_text(
            "🌍 **Set Your Timezone**\n\n"
            "Usage: /timezone <IANA_timezone>\n\n"
            "Examples:\n"
            "• /timezone Europe/Rome\n"
            "• /timezone America/New_York\n"
            "• /timezone Asia/Tokyo\n\n"
            "Or just send the timezone name."
        )
        return
    
    tz_str = context.args[0]
    
    if not validate_timezone(tz_str):
        await update.message.reply_text(
            "⚠️ Invalid timezone!\n\n"
            "Please use a valid IANA timezone.\n"
            "Examples: Europe/Rome, America/New_York, Asia/Tokyo"
        )
        return
    
    # Update in database
    db.update_user_timezone(user_id, tz_str)
    
    # Reschedule reminder
    reschedule_user_reminder(context.application, user_id)
    
    await update.message.reply_text(
        f"✅ Timezone set to {tz_str}!"
    )
    
    logger.info(f"User {user_id} set timezone to {tz_str}")


async def btn_set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Set Timezone button."""
    await update.message.reply_text(
        "🌍 **Set Your Timezone**\n\n"
        "Please send your timezone using IANA format.\n\n"
        "Examples:\n"
        "• Europe/Rome\n"
        "• America/New_York\n"
        "• Asia/Tokyo\n"
        "• UTC"
    )


# Inline callback handlers
async def callback_refresh_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Refresh' inline button callback."""
    query = update.callback_query
    await query.answer("Refreshing...")
    
    user_id = update.effective_user.id
    user = db.get_or_create_user(user_id)
    exams = db.get_user_exams(user_id)
    
    if not exams:
        await query.edit_message_text(
            "📋 You have no exams yet.\n\n"
            "Use ➕ Add Exam to add your first exam!"
        )
        return
    
    # Build message
    lines = ["📋 **Your Exams:**\n"]
    for exam in exams:
        countdown_msg, days = format_exam_countdown(
            exam['exam_datetime_iso'],
            user['timezone']
        )
        lines.append(
            f"🆔 {exam['user_exam_id']}: **{exam['title']}**\n"
            f"   📅 {exam['exam_datetime_iso'].replace('T', ' ')}\n"
            f"   ⏳ {countdown_msg}\n"
        )
    
    message_text = '\n'.join(lines)
    
    # Update message
    keyboard = get_exam_list_inline_keyboard(exams, show_delete_buttons=False)
    
    await query.edit_message_text(
        message_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )


async def callback_notify_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Notify Now' inline button callback."""
    query = update.callback_query
    await query.answer("Sending notification...")
    
    user_id = update.effective_user.id
    user = db.get_or_create_user(user_id)
    exams = db.get_user_exams(user_id)
    
    # Generate message
    message = get_upcoming_exams_message(exams, user['timezone'])
    
    if message:
        await context.bot.send_message(
            chat_id=user_id,
            text=message
        )
        logger.info(f"Manual notification sent to user {user_id}")
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text="ℹ️ You have no upcoming exams."
        )


async def callback_delete_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline delete button callback."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Extract exam_id from callback_data (format: "del:123")
    callback_data = query.data
    if not callback_data.startswith("del:"):
        await query.answer("Invalid callback data")
        return
    
    try:
        exam_id = int(callback_data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.answer("Invalid exam ID")
        return
    
    # Delete exam
    success = db.delete_exam(exam_id, user_id)
    
    if success:
        await query.answer(f"Exam #{exam_id} deleted!")
        logger.info(f"User {user_id} deleted exam {exam_id} via inline button")
        
        # Refresh the list
        user = db.get_or_create_user(user_id)
        exams = db.get_user_exams(user_id)
        
        if not exams:
            await query.edit_message_text(
                "✅ Exam deleted!\n\n"
                "📋 You have no more exams."
            )
            return
        
        # Build updated message
        lines = ["✅ Exam deleted!\n\n🗑 **Select exam to delete:**\n"]
        for exam in exams[:10]:
            countdown_msg, _ = format_exam_countdown(
                exam['exam_datetime_iso'],
                user['timezone']
            )
            lines.append(
                f"🆔 {exam['user_exam_id']}: {exam['title']}\n"
                f"   📅 {exam['exam_datetime_iso'].replace('T', ' ')}\n"
                f"   ⏳ {countdown_msg}\n"
            )
        
        message_text = '\n'.join(lines)
        keyboard = get_exam_list_inline_keyboard(exams, show_delete_buttons=True)
        
        await query.edit_message_text(
            message_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        await query.answer("Exam not found or already deleted", show_alert=True)


# Handler for time input after button press
async def handle_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle time input when user is setting notification time."""
    text = update.message.text.strip()
    
    # Check if it's a valid time format
    normalized_time = parse_time(text)
    if normalized_time:
        user_id = update.effective_user.id
        db.update_user_notify_time(user_id, normalized_time)
        
        try:
            reschedule_user_reminder(context.application, user_id)
            logger.info(f"User {user_id} rescheduled notification to {normalized_time}")
        except Exception as e:
            logger.error(f"Failed to reschedule for user {user_id}: {e}")
        
        await update.message.reply_text(
            f"✅ Daily notification time set to {normalized_time}!",
            reply_markup=get_main_menu_keyboard()
        )
        logger.info(f"User {user_id} set notification time to {normalized_time}")
        return


# Handler for timezone input after button press
async def handle_timezone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle timezone input when user is setting timezone."""
    text = update.message.text.strip()
    
    # Check if it's a valid timezone
    if validate_timezone(text):
        user_id = update.effective_user.id
        db.update_user_timezone(user_id, text)
        reschedule_user_reminder(context.application, user_id)
        
        await update.message.reply_text(
            f"✅ Timezone set to {text}!",
            reply_markup=get_main_menu_keyboard()
        )
        logger.info(f"User {user_id} set timezone to {text}")
        return


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /broadcast command - Send a message to all users.
    Only available to admin.
    """
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id != Config.ADMIN_ID:
        await update.message.reply_text("⛔ This command is only available to the admin.")
        return
    
    # Check if message is provided
    if not context.args:
        await update.message.reply_text(
            "📢 **Broadcast Message**\n\n"
            "Usage: `/broadcast Your message here`\n\n"
            "This will send the message to ALL users.",
            parse_mode='Markdown'
        )
        return
    
    # Get the message
    message_text = ' '.join(context.args)
    
    # Get all users
    users = db.get_all_users()
    
    if not users:
        await update.message.reply_text("⚠️ No users found in database.")
        return
    
    # Send status message
    status_msg = await update.message.reply_text(
        f"📤 Sending message to {len(users)} users..."
    )
    
    # Send to all users
    success_count = 0
    fail_count = 0
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"📢 **Announcement**\n\n{message_text}",
                parse_mode='Markdown'
            )
            success_count += 1
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.05)
        except Exception as e:
            fail_count += 1
            logger.warning(f"Failed to send broadcast to {user['user_id']}: {e}")
    
    # Update status
    await status_msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"📨 Sent: {success_count}\n"
        f"❌ Failed: {fail_count}\n"
        f"👥 Total: {len(users)}",
        parse_mode='Markdown'
    )
    
    logger.info(f"Admin {user_id} broadcasted message to {success_count}/{len(users)} users")
