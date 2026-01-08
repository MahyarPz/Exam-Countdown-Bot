"""Keyboard layouts for the bot."""

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get the main menu Reply Keyboard."""
    keyboard = [
        ["➕ Add Exam", "📋 List Exams"],
        ["🗑 Delete Exam", "⏰ Set Daily Time"],
        ["🌍 Set Timezone", "💬 Feedback"],
        ["ℹ️ Help"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_exam_list_inline_keyboard(exams: List[Dict[str, Any]], show_delete_buttons: bool = False) -> InlineKeyboardMarkup:
    """
    Get inline keyboard for exam list.
    
    Args:
        exams: List of exam dictionaries
        show_delete_buttons: If True, add delete button for each exam
    """
    buttons = []
    
    # Add delete button for each exam (limit to first 10)
    if show_delete_buttons and exams:
        for exam in exams[:10]:
            buttons.append([
                InlineKeyboardButton(
                    f"🗑 Delete #{exam['user_exam_id']} - {exam['title'][:30]}",
                    callback_data=f"del:{exam['user_exam_id']}"
                )
            ])
    
    # Add action buttons
    action_buttons = [
        InlineKeyboardButton("🔄 Refresh", callback_data="refresh_list"),
        InlineKeyboardButton("🔔 Notify Now", callback_data="notify_now")
    ]
    buttons.append(action_buttons)
    
    return InlineKeyboardMarkup(buttons)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Get a keyboard with just a cancel button."""
    keyboard = [["❌ Cancel"]]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
