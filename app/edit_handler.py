"""Conversation handler for Edit Exam flow."""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from app import db
from app.utils import parse_exam_datetime, format_exam_countdown
from app.keyboards import (
    get_main_menu_keyboard,
    get_cancel_keyboard,
    get_exam_edit_inline_keyboard,
    get_edit_field_keyboard
)

logger = logging.getLogger(__name__)

# Conversation states
SELECT_EXAM, SELECT_FIELD, EDIT_TITLE, EDIT_DATETIME = range(4)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    from app.config import Config
    return user_id == Config.ADMIN_ID


async def start_edit_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the edit exam conversation - show list of exams to edit."""
    user_id = update.effective_user.id
    user = db.get_or_create_user(user_id)
    exams = db.get_user_exams(user_id)
    
    if not exams:
        await update.message.reply_text(
            "📋 You have no exams to edit.\n\n"
            "Use ➕ Add Exam to add your first exam!",
            reply_markup=get_main_menu_keyboard(is_admin(user_id))
        )
        return ConversationHandler.END
    
    # Build message with exam list
    lines = ["✏️ **Select exam to edit:**\n"]
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
    keyboard = get_exam_edit_inline_keyboard(exams)
    
    await update.message.reply_text(
        message_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    
    return SELECT_EXAM


async def select_exam_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle exam selection callback."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    # Handle cancel
    if callback_data == "edit_cancel":
        await query.edit_message_text(
            "❌ Edit cancelled.",
        )
        return ConversationHandler.END
    
    # Extract exam_id from callback_data (format: "edit:123")
    if not callback_data.startswith("edit:"):
        await query.answer("Invalid selection")
        return SELECT_EXAM
    
    try:
        exam_id = int(callback_data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.answer("Invalid exam ID")
        return SELECT_EXAM
    
    # Get exam details
    exam = db.get_exam_by_id(exam_id, user_id)
    
    if not exam:
        await query.edit_message_text(
            "⚠️ Exam not found. It may have been deleted."
        )
        return ConversationHandler.END
    
    # Store exam_id in context
    context.user_data['edit_exam_id'] = exam_id
    context.user_data['edit_exam_title'] = exam['title']
    
    # Show field selection
    await query.edit_message_text(
        f"✏️ **Editing Exam #{exam_id}:**\n\n"
        f"📚 Title: {exam['title']}\n"
        f"📅 Date: {exam['exam_datetime_iso'].replace('T', ' ')}\n\n"
        f"What do you want to edit?",
        parse_mode='Markdown',
        reply_markup=get_edit_field_keyboard(exam_id)
    )
    
    return SELECT_FIELD


async def select_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle field selection callback."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Handle cancel
    if callback_data == "edit_cancel":
        await query.edit_message_text("❌ Edit cancelled.")
        context.user_data.clear()
        return ConversationHandler.END
    
    # Extract field from callback_data (format: "editfield:123:title" or "editfield:123:datetime")
    if not callback_data.startswith("editfield:"):
        await query.answer("Invalid selection")
        return SELECT_FIELD
    
    try:
        parts = callback_data.split(":")
        exam_id = int(parts[1])
        field = parts[2]
    except (ValueError, IndexError):
        await query.answer("Invalid selection")
        return SELECT_FIELD
    
    context.user_data['edit_exam_id'] = exam_id
    context.user_data['edit_field'] = field
    
    if field == "title":
        await query.edit_message_text(
            f"📝 **Edit Title**\n\n"
            f"Current title: {context.user_data.get('edit_exam_title', 'N/A')}\n\n"
            f"Send the new title:",
            parse_mode='Markdown'
        )
        return EDIT_TITLE
    
    elif field == "datetime":
        await query.edit_message_text(
            f"📅 **Edit Date/Time**\n\n"
            f"Send the new date in one of these formats:\n"
            f"• YYYY-MM-DD (e.g., 2026-01-15)\n"
            f"• YYYY-MM-DD HH:MM (e.g., 2026-01-15 14:30)\n\n"
            f"If you don't specify time, it defaults to 09:00.",
            parse_mode='Markdown'
        )
        return EDIT_DATETIME
    
    return SELECT_FIELD


async def receive_new_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive new exam title."""
    new_title = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Check for cancel
    if new_title == "❌ Cancel":
        await update.message.reply_text(
            "❌ Edit cancelled.",
            reply_markup=get_main_menu_keyboard(is_admin(user_id))
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    if not new_title:
        await update.message.reply_text(
            "⚠️ Title cannot be empty. Please send the new title:"
        )
        return EDIT_TITLE
    
    exam_id = context.user_data.get('edit_exam_id')
    
    # Update in database
    success = db.update_exam(exam_id, user_id, title=new_title)
    
    if success:
        await update.message.reply_text(
            f"✅ Exam title updated successfully!\n\n"
            f"📚 New title: {new_title}",
            reply_markup=get_main_menu_keyboard(is_admin(user_id))
        )
        logger.info(f"User {user_id} updated exam {exam_id} title to: {new_title}")
    else:
        await update.message.reply_text(
            f"⚠️ Failed to update exam. Please try again.",
            reply_markup=get_main_menu_keyboard(is_admin(user_id))
        )
    
    context.user_data.clear()
    return ConversationHandler.END


async def receive_new_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive new exam date/time."""
    date_str = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Check for cancel
    if date_str == "❌ Cancel":
        await update.message.reply_text(
            "❌ Edit cancelled.",
            reply_markup=get_main_menu_keyboard(is_admin(user_id))
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
            "Try again:"
        )
        return EDIT_DATETIME
    
    exam_id = context.user_data.get('edit_exam_id')
    
    # Update in database
    success = db.update_exam(exam_id, user_id, exam_datetime_iso=exam_datetime_iso)
    
    if success:
        await update.message.reply_text(
            f"✅ Exam date updated successfully!\n\n"
            f"📅 New date: {exam_datetime_iso.replace('T', ' ')}",
            reply_markup=get_main_menu_keyboard(is_admin(user_id))
        )
        logger.info(f"User {user_id} updated exam {exam_id} datetime to: {exam_datetime_iso}")
    else:
        await update.message.reply_text(
            f"⚠️ Failed to update exam. Please try again.",
            reply_markup=get_main_menu_keyboard(is_admin(user_id))
        )
    
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the edit conversation."""
    user_id = update.effective_user.id
    await update.message.reply_text(
        "❌ Edit cancelled.",
        reply_markup=get_main_menu_keyboard(is_admin(user_id))
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_edit_exam_conversation_handler() -> ConversationHandler:
    """Create and return the ConversationHandler for editing exams."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^✏️ Edit Exam$"), start_edit_exam),
            CommandHandler("edit", start_edit_exam)
        ],
        states={
            SELECT_EXAM: [
                CallbackQueryHandler(select_exam_callback, pattern="^edit:|^edit_cancel$")
            ],
            SELECT_FIELD: [
                CallbackQueryHandler(select_field_callback, pattern="^editfield:|^edit_cancel$")
            ],
            EDIT_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_title)
            ],
            EDIT_DATETIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_datetime)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_edit),
            MessageHandler(filters.Regex("^❌ Cancel$"), cancel_edit)
        ],
        name="edit_exam_conversation",
        persistent=False
    )
