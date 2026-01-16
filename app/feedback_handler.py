"""Feedback handler for user feedback system."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        "💬 **Send your feedback or suggestion:**\n\n"
        "Please type your message or /cancel to abort.",
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
            "❌ Cancelled.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    if not feedback_text:
        await update.message.reply_text(
            "⚠️ Message cannot be empty. Please try again:",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_FEEDBACK
    
    # Send to admin
    admin_id = Config.ADMIN_ID
    if admin_id <= 0:
        logger.warning("ADMIN_ID not configured. Feedback not sent.")
        await update.message.reply_text(
            "❌ Error: Admin not configured.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Format message for admin (using HTML for better compatibility)
    username_display = f"@{user.username}" if user.username else "N/A"
    admin_message = (
        f"📨 <b>New Feedback:</b>\n\n"
        f"👤 Name: {user.first_name} {user.last_name or ''}\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"📱 Username: {username_display}\n\n"
        f"💬 <b>Message:</b>\n{feedback_text}"
    )
    
    # Create reply button
    reply_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Reply", callback_data=f"reply:{user.id}")]
    ])
    
    try:
        await context.bot.send_message(
            chat_id=admin_id,
            text=admin_message,
            parse_mode='HTML',
            reply_markup=reply_keyboard
        )
        
        # Confirm to user
        await update.message.reply_text(
            "✅ **Your feedback has been sent successfully.**\n\n"
            "Thank you!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        logger.info(f"Feedback from user {user.id} ({user.first_name}): {feedback_text[:50]}...")
        
    except Exception as e:
        logger.error(f"Error sending feedback to admin {admin_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Error sending feedback. Please try again.",
            reply_markup=get_main_menu_keyboard()
        )
    
    return ConversationHandler.END


async def cancel_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the feedback conversation."""
    await update.message.reply_text(
        "❌ Cancelled.",
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
