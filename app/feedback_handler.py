"""Feedback handler for user feedback system."""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from app.config import Config
from app.keyboards import get_main_menu_keyboard, get_cancel_keyboard

logger = logging.getLogger(__name__)

# Conversation states
ASK_FEEDBACK = 0


async def start_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the feedback conversation."""
    user = update.effective_user
    
    await update.message.reply_text(
        "💬 **نظر یا پیشنهادتان را برایم بنویسید:**\n\n"
        "لطفاً پیام خود را تایپ کنید یا /cancel برای انصراف.",
        reply_markup=get_cancel_keyboard(),
        parse_mode='Markdown'
    )
    return ASK_FEEDBACK


async def receive_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive feedback and forward to admin."""
    user = update.effective_user
    feedback_text = update.message.text.strip()
    
    # Check for cancel
    if feedback_text == "❌ Cancel":
        await update.message.reply_text(
            "❌ لغو شد.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    if not feedback_text:
        await update.message.reply_text(
            "⚠️ پیام نمی‌تواند خالی باشد. لطفاً دوباره سعی کنید:",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_FEEDBACK
    
    # Send to admin
    admin_id = Config.ADMIN_ID
    if admin_id <= 0:
        logger.warning("ADMIN_ID not configured. Feedback not sent.")
        await update.message.reply_text(
            "❌ خطا: ادمین تنظیم نشده است.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Format message for admin
    admin_message = (
        f"📨 **نظر جدید از کاربر:**\n\n"
        f"👤 نام: {user.first_name} {user.last_name or ''}\n"
        f"🆔 User ID: {user.id}\n"
        f"📱 Username: @{user.username or 'ندارد'}\n\n"
        f"💬 **متن نظر:**\n{feedback_text}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=admin_id,
            text=admin_message,
            parse_mode='Markdown'
        )
        
        # Confirm to user
        await update.message.reply_text(
            "✅ **نظر شما با موفقیت ارسال شد.**\n\n"
            "متشکریم!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        logger.info(f"Feedback from user {user.id} ({user.first_name}): {feedback_text[:50]}...")
        
    except Exception as e:
        logger.error(f"Error sending feedback to admin {admin_id}: {e}")
        await update.message.reply_text(
            "❌ خطا در ارسال نظر. لطفاً دوباره سعی کنید.",
            reply_markup=get_main_menu_keyboard()
        )
    
    return ConversationHandler.END


async def cancel_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the feedback conversation."""
    await update.message.reply_text(
        "❌ لغو شد.",
        reply_markup=get_main_menu_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_feedback_conversation_handler() -> ConversationHandler:
    """Create and return the ConversationHandler for feedback."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💬 Feedback$"), start_feedback),
            CommandHandler("feedback", start_feedback)
        ],
        states={
            ASK_FEEDBACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_feedback)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_feedback),
            MessageHandler(filters.Regex("^❌ Cancel$"), cancel_feedback)
        ],
        name="feedback_conversation",
        persistent=False
    )
