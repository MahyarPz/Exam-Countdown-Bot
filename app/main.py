"""Main entry point for the Exam Countdown Bot."""

import asyncio
import logging
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from app.config import Config
from app import db
from app.handlers import (
    cmd_start,
    cmd_menu,
    cmd_help,
    cmd_add,
    cmd_list,
    cmd_delete,
    cmd_settime,
    cmd_timezone,
    cmd_debug,
    cmd_schedule,
    cmd_broadcast,
    cmd_stats,
    cmd_reply,
    btn_delete_exam,
    btn_set_time,
    btn_set_timezone,
    btn_broadcast,
    btn_debug,
    btn_schedule,
    btn_stats,
    callback_refresh_list,
    callback_notify_now,
    callback_delete_exam,
    callback_reply_button,
    handle_admin_reply,
    handle_time_input,
    handle_timezone_input
)
from app.conversations import get_add_exam_conversation_handler
from app.feedback_handler import get_feedback_conversation_handler
from app.edit_handler import get_edit_exam_conversation_handler
from app.scheduler import schedule_all_users

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    try:
        # Initialize database
        db.init_db()
        if Config.use_postgres():
            logger.info("Using PostgreSQL database")
        else:
            logger.info("Using SQLite database")
        
        # Create application
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Add conversation handler for Add Exam flow
        application.add_handler(get_add_exam_conversation_handler())
        
        # Add conversation handler for Edit Exam flow
        application.add_handler(get_edit_exam_conversation_handler())
        
        # Add conversation handler for Feedback flow
        application.add_handler(get_feedback_conversation_handler())
        
        # Add command handlers
        application.add_handler(CommandHandler("start", cmd_start))
        application.add_handler(CommandHandler("menu", cmd_menu))
        application.add_handler(CommandHandler("help", cmd_help))
        application.add_handler(CommandHandler("add", cmd_add))
        application.add_handler(CommandHandler("list", cmd_list))
        application.add_handler(CommandHandler("delete", cmd_delete))
        application.add_handler(CommandHandler("settime", cmd_settime))
        application.add_handler(CommandHandler("timezone", cmd_timezone))
        application.add_handler(CommandHandler("debug", cmd_debug))
        application.add_handler(CommandHandler("schedule", cmd_schedule))
        application.add_handler(CommandHandler("broadcast", cmd_broadcast))
        application.add_handler(CommandHandler("stats", cmd_stats))
        application.add_handler(CommandHandler("reply", cmd_reply))
        
        # Add button handlers (Reply Keyboard)
        application.add_handler(MessageHandler(
            filters.Regex("^📋 List Exams$"),
            cmd_list
        ))
        application.add_handler(MessageHandler(
            filters.Regex("^🗑 Delete Exam$"),
            btn_delete_exam
        ))
        application.add_handler(MessageHandler(
            filters.Regex("^⏰ Set Daily Time$"),
            btn_set_time
        ))
        application.add_handler(MessageHandler(
            filters.Regex("^🌍 Set Timezone$"),
            btn_set_timezone
        ))
        application.add_handler(MessageHandler(
            filters.Regex("^ℹ️ Help$"),
            cmd_help
        ))
        # Note: "💬 Feedback" is handled by get_feedback_conversation_handler()
        
        # Admin button handlers
        application.add_handler(MessageHandler(
            filters.Regex("^📢 Broadcast$"),
            btn_broadcast
        ))
        application.add_handler(MessageHandler(
            filters.Regex("^🔧 Debug$"),
            btn_debug
        ))
        application.add_handler(MessageHandler(
            filters.Regex("^📅 Schedule$"),
            btn_schedule
        ))
        application.add_handler(MessageHandler(
            filters.Regex("^📊 Stats$"),
            btn_stats
        ))
        
        # Add inline callback handlers
        application.add_handler(CallbackQueryHandler(
            callback_refresh_list,
            pattern="^refresh_list$"
        ))
        application.add_handler(CallbackQueryHandler(
            callback_notify_now,
            pattern="^notify_now$"
        ))
        application.add_handler(CallbackQueryHandler(
            callback_delete_exam,
            pattern="^del:"
        ))
        application.add_handler(CallbackQueryHandler(
            callback_reply_button,
            pattern="^reply:"
        ))
        
        # Add handler for admin reply (must be before other text handlers)
        async def combined_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Handle text input - check admin reply first, then time/timezone."""
            text = update.message.text
            
            # Skip menu button texts - let conversation handlers handle them
            menu_buttons = [
                "➕ Add Exam", "📋 List Exams", "🗑 Delete Exam",
                "⏰ Set Daily Time", "🌍 Set Timezone", "ℹ️ Help",
                "💬 Feedback", "❌ Cancel", "📢 Broadcast",
                "🔧 Debug", "📅 Schedule", "📊 Stats", "✏️ Edit Exam"
            ]
            if text in menu_buttons:
                return
            
            # First check if it's an admin reply
            if await handle_admin_reply(update, context):
                return
            
            # Then try time input
            await handle_time_input(update, context)
            
            # Then try timezone input
            await handle_timezone_input(update, context)
        
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            combined_text_handler
        ))
        
        # Schedule reminders for all users
        schedule_all_users(application)
        
        # Start the bot
        logger.info("Starting bot...")
        if Config.DEBUG_FAST_SCHEDULE:
            logger.warning("DEBUG_FAST_SCHEDULE is enabled - notifications every 60 seconds!")
        
        print("\n" + "="*50)
        print("🤖 Bot started successfully!")
        print("="*50)
        if Config.DEBUG_FAST_SCHEDULE:
            print("⚠️  DEBUG MODE: Fast schedule enabled (60s intervals)")
        print("Press Ctrl+C to stop the bot")
        print("="*50 + "\n")
        
        application.run_polling(allowed_updates=["message", "callback_query"])
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n👋 Bot stopped. Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Fix for Python 3.10+ - create event loop before running
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    main()
