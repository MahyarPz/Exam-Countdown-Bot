# Exam Countdown Bot - AI Coding Guidelines

## Project Overview

A Telegram bot for managing exam dates with daily countdown notifications. Built with `python-telegram-bot` v21+ (async API) supporting three database backends: SQLite (default), PostgreSQL, and Google Firestore.

## Architecture

```
app/
├── main.py          # Entry point, handler registration, polling loop
├── config.py        # Environment-based configuration (Config class)
├── db.py            # Database abstraction layer (auto-selects backend)
├── firestore_db.py  # Firestore-specific implementation
├── handlers.py      # Command & callback handlers (cmd_*, btn_*, callback_*)
├── conversations.py # Multi-step conversation flows (ConversationHandler)
├── edit_handler.py  # Edit exam conversation flow
├── feedback_handler.py # User feedback conversation flow
├── scheduler.py     # APScheduler-based daily reminder jobs
├── keyboards.py     # Telegram keyboard layouts (Reply & Inline)
└── utils.py         # Date parsing, timezone validation, formatting
```

### Key Design Patterns

- **Database abstraction**: `db.py` delegates to `firestore_db.py` when `Config.use_firestore()` is true, otherwise uses SQLite/PostgreSQL via context manager
- **Handler naming**: Commands use `cmd_` prefix, button handlers use `btn_` prefix, callbacks use `callback_` prefix
- **Conversation states**: Defined as module-level constants (e.g., `ASK_TITLE, ASK_DATETIME = range(2)`)

## Running the Bot

```bash
# Standard mode
python -m app.main

# Debug mode (notifications every 60s instead of daily)
# Set DEBUG_FAST_SCHEDULE=1 in .env
python -m app.main
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram bot token from @BotFather |
| `ADMIN_ID` | No | Telegram user ID for admin features |
| `DATABASE_URL` | No | PostgreSQL connection string |
| `USE_FIRESTORE` | No | Set to `1` to enable Firestore |
| `FIREBASE_PROJECT_ID` | No* | Required if USE_FIRESTORE=1 |
| `DEBUG_FAST_SCHEDULE` | No | Set to `1` for 60s notification intervals |

## Adding New Features

### Adding a Command Handler

1. Add handler function in [handlers.py](app/handlers.py) following the pattern:
```python
async def cmd_newcommand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # Use db.get_or_create_user(user_id) to ensure user exists
    await update.message.reply_text("Response", reply_markup=get_main_menu_keyboard())
```

2. Register in [main.py](app/main.py):
```python
application.add_handler(CommandHandler("newcommand", cmd_newcommand))
```

### Adding a Menu Button

1. Add button text in [keyboards.py](app/keyboards.py) `get_main_menu_keyboard()`
2. Add message handler in [main.py](app/main.py) with `filters.Regex("^🆕 Button Text$")`

### Adding a Conversation Flow

Follow the pattern in [conversations.py](app/conversations.py):
- Define states as `range()` constants
- Return state integers to continue, `ConversationHandler.END` to finish
- Always handle the "❌ Cancel" button text

### Database Operations

All database functions are in [db.py](app/db.py). When adding new operations:
- Add the function to `db.py` for SQLite/PostgreSQL
- Add equivalent in `firestore_db.py` if using Firestore
- Use `Config.use_firestore()` check to delegate appropriately

## Code Conventions

- **Timezone handling**: Always use `pytz` for validation, `ZoneInfo` for scheduler
- **Date storage**: Store as ISO format strings (`exam_datetime_iso`)
- **User IDs**: Use `user_exam_id` (per-user sequential) not global `id` for user-facing references
- **Async**: All handler functions must be `async def` (python-telegram-bot v21+)
- **Logging**: Use module-level logger: `logger = logging.getLogger(__name__)`

## Admin Features

Admin commands are gated by `ADMIN_ID` env var. Check pattern in [handlers.py](app/handlers.py):
```python
if not is_admin(user_id):  # Uses Config.ADMIN_ID comparison
    await update.message.reply_text("⛔ This command is only available to the admin.")
    return
```

**Available admin commands:**
- `/broadcast <message>` - Send announcement to all users (includes rate-limit delay)
- `/stats` - Show user/exam counts
- `/reply <user_id> <message>` - Reply to user feedback
- `/debug` - Scheduler job inspection
- `/schedule` - Force-create reminder job

Admin menu buttons appear automatically when `is_admin(user_id)` returns true in `get_main_menu_keyboard()`.

## Database Migrations

Schema changes use the pattern in [db.py](app/db.py) `_ensure_user_exam_id()`:

1. Check if column exists with `_has_column(cursor, table_name, column_name)`
2. Add column with `ALTER TABLE` if missing
3. Backfill data for existing rows
4. Create indexes
5. Wrap in try/except with `conn.rollback()` on failure

Migration runs automatically in `init_db()`. For Firestore, handle schema evolution in document writes (schemaless).

## Deployment (Heroku)

**Key files:**
- `Procfile`: `worker: python -m app.main` (not `web` - bot uses polling, not webhooks)
- `runtime.txt`: Python version specification
- `requirements.txt`: All dependencies

**Deploy commands:**
```bash
heroku create your-app-name
heroku config:set BOT_TOKEN=your_token
heroku config:set ADMIN_ID=your_telegram_id
# For Firestore: set USE_FIRESTORE=1, FIREBASE_PROJECT_ID, FIREBASE_CREDENTIALS
git push heroku main
heroku ps:scale worker=1
```

**Database options on Heroku:**
- PostgreSQL: Add `heroku-postgresql` addon, `DATABASE_URL` auto-configured
- Firestore: Set `FIREBASE_CREDENTIALS` as single-line JSON string

## Testing

Manual testing guide available in [TESTING.md](TESTING.md). Key test scenarios:
1. Enable `DEBUG_FAST_SCHEDULE=1` for rapid notification testing (60s intervals)
2. Use `/debug` command to inspect scheduled jobs
3. Use `/schedule` command to force-create a job
