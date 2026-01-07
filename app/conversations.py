"""Conversation handler for Add Exam flow."""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from app import db
from app.utils import parse_exam_datetime
from app.keyboards import get_main_menu_keyboard, get_cancel_keyboard

logger = logging.getLogger(__name__)

# Conversation states
ASK_TITLE, ASK_DATETIME = range(2)


async def start_add_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the add exam conversation."""
    # Ensure user exists in DB
    db.get_or_create_user(update.effective_user.id)
    
    await update.message.reply_text(
        "📝 Let's add a new exam!\n\n"
        "What's the exam title?",
        reply_markup=get_cancel_keyboard()
    )
    return ASK_TITLE


async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive exam title and ask for date/time."""
    title = update.message.text.strip()
    
    # Check for cancel
    if title == "❌ Cancel":
        await update.message.reply_text(
            "❌ Cancelled adding exam.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    if not title:
        await update.message.reply_text(
            "⚠️ Title cannot be empty. Please send the exam title:",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_TITLE
    
    # Store title in context
    context.user_data['exam_title'] = title
    
    await update.message.reply_text(
        f"📅 Great! Now when is the exam?\n\n"
        f"Send the date in one of these formats:\n"
        f"• YYYY-MM-DD (e.g., 2026-01-15)\n"
        f"• YYYY-MM-DD HH:MM (e.g., 2026-01-15 14:30)\n\n"
        f"If you don't specify time, it defaults to 09:00.",
        reply_markup=get_cancel_keyboard()
    )
    return ASK_DATETIME


async def receive_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive exam date/time and save to database."""
    date_str = update.message.text.strip()
    
    # Check for cancel
    if date_str == "❌ Cancel":
        await update.message.reply_text(
            "❌ Cancelled adding exam.",
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Parse datetime
    exam_datetime_iso = parse_exam_datetime(date_str)
    
    if not exam_datetime_iso:
        await update.message.reply_text(
            "⚠️ Invalid date format!\n\n"
            "Please use one of these formats:\n"
            "• YYYY-MM-DD (e.g., 2026-01-15)\n"
            "• YYYY-MM-DD HH:MM (e.g., 2026-01-15 14:30)\n\n"
            "Try again:",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_DATETIME
    
    # Get title from context
    title = context.user_data.get('exam_title')
    user_id = update.effective_user.id
    
    # Save to database
    exam_id = db.add_exam(user_id, title, exam_datetime_iso)
    
    await update.message.reply_text(
        f"✅ Exam added successfully!\n\n"
        f"📚 {title}\n"
        f"📅 {exam_datetime_iso.replace('T', ' ')}\n"
        f"🆔 ID: {exam_id}",
        reply_markup=get_main_menu_keyboard()
    )
    
    # Clear context
    context.user_data.clear()
    
    logger.info(f"User {user_id} added exam: {title} on {exam_datetime_iso}")
    
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "❌ Operation cancelled.",
        reply_markup=get_main_menu_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_add_exam_conversation_handler() -> ConversationHandler:
    """Create and return the ConversationHandler for adding exams."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Add Exam$"), start_add_exam),
            CommandHandler("add_start", start_add_exam)
        ],
        states={
            ASK_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)
            ],
            ASK_DATETIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_datetime)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.Regex("^❌ Cancel$"), cancel_conversation)
        ],
        name="add_exam_conversation",
        persistent=False
    )
