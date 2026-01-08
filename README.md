# Exam Countdown Bot

A production-ready Telegram bot for managing exam dates and receiving daily countdown notifications. Supports SQLite, PostgreSQL, and Google Firestore.

## Features

- 📅 Manage multiple exams with dates and times
- ⏰ Daily countdown notifications at customizable time
- 🌍 Timezone support (IANA timezones)
- 🎯 Reply Keyboard for easy navigation
- ⚡ Inline buttons for quick actions
- 💬 User feedback system with admin notifications
- 💾 Multi-database support:
  - SQLite (default, local)
  - PostgreSQL (recommended for production)
  - Google Firestore (cloud-based)
- 🔄 Always-on polling with async support

## Requirements

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Optional: Google Firebase/Firestore account (for cloud database)

## Installation

1. **Clone and navigate to the project:**
   ```bash
   cd exam_countdown_bot
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Choose your database option and add configuration

### Database Configuration Options

#### Option 1: SQLite (Default - No Setup Needed)
Use this for testing or small deployments. Data is stored in `exam_bot.db` locally.

#### Option 2: PostgreSQL
For production deployments:
```bash
# Add to .env:
DATABASE_URL=postgresql://user:password@localhost:5432/exam_bot
```

#### Option 3: Google Firestore (Cloud-Based)
Best for cloud deployments like Heroku:

1. **Create Firebase project:**
   - Go to [Firebase Console](https://console.firebase.google.com)
   - Create a new project
   - Copy Project ID

2. **Create service account:**
   - Go to Project Settings → Service Accounts
   - Click "Generate New Private Key" (JSON)
   - Save the JSON file

3. **For Local Development:**
   ```bash
   # Add to .env:
   USE_FIRESTORE=1
   FIREBASE_PROJECT_ID=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-key.json
   ```

4. **For Heroku:**
   ```bash
   # Convert JSON to single line (no newlines) and add to Config Vars:
   FIREBASE_CREDENTIALS='{"type":"service_account","project_id":"..."...}'
   USE_FIRESTORE=1
   FIREBASE_PROJECT_ID=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=/tmp/firebase-key.json
   ```

5. **Add to Procfile** (if needed):
   ```
   web: python -m app.main
   ```

## Running the Bot

**Normal mode (daily notifications):**
```bash
python -m app.main
```

**Debug mode (notifications every 60 seconds):**
```bash
# Set in .env: DEBUG_FAST_SCHEDULE=1
python -m app.main
```

The bot will start polling and display "Bot started successfully!"

## Usage

### Reply Keyboard Menu

After `/start`, you'll see a menu with buttons:
- **➕ Add Exam** - Start conversation to add a new exam
- **📋 List Exams** - Show all your exams with inline actions
- **🗑 Delete Exam** - Show list with delete buttons
- **⏰ Set Daily Time** - Change notification time (HH:MM format)
- **🌍 Set Timezone** - Set your timezone (e.g., Europe/Rome, America/New_York)
- **💬 Feedback** - Send feedback to admin
- **ℹ️ Help** - Show help message

### Commands (Alternative)

You can also use traditional commands:
- `/start` - Initialize bot and show menu
- `/menu` - Show reply keyboard menu
- `/add <title> | <YYYY-MM-DD or YYYY-MM-DD HH:MM>` - Add exam
- `/list` - List all exams
- `/delete <id>` - Delete exam by ID
- `/settime <HH:MM>` - Set daily notification time (e.g., 09:00)
- `/timezone <IANA_TZ>` - Set timezone (e.g., Europe/Rome)
- `/help` - Show help

### Add Exam Flow (via Button)

1. Tap "➕ Add Exam"
2. Bot asks: "What's the exam title?"
3. Send exam name (e.g., "Mathematics Final")
4. Bot asks: "When is the exam?"
5. Send date in format:
   - `YYYY-MM-DD` (time defaults to 09:00)
   - `YYYY-MM-DD HH:MM` (specific time)
6. Bot confirms and saves

### Inline Buttons

When you use "📋 List Exams", you'll see:
- **Delete #ID** button for each exam (quick delete)
- **Refresh** button - Refresh the list
- **Notify Now** button - Test notification immediately

### Daily Notifications

The bot sends daily reminders at your configured time:
```
📚 Exam reminder:
- Mathematics Final — 5 days left
- Physics Exam — 12 days left
- Chemistry Test — today
```

No message is sent if you have no upcoming exams.

## Testing

### Quick Manual Test

1. **Start bot:**
   ```bash
   python -m app.main
   ```

2. **In Telegram:**
   - Send `/start` - Should see welcome message and menu keyboard
   - Tap "➕ Add Exam"
   - Send "Test Exam"
   - Send a future date: `2026-01-15`
   - Confirm exam is added

3. **Test list with inline buttons:**
   - Tap "📋 List Exams"
   - Should see exam with "Delete #1", "Refresh", "Notify Now" buttons
   - Tap "Notify Now" - Should receive immediate notification
   - Tap "Refresh" - List should update

4. **Test inline delete:**
   - Tap "Delete #1" button
   - Exam should be deleted and list refreshed

5. **Test timezone and time:**
   - Tap "⏰ Set Daily Time"
   - Send `10:30`
   - Tap "🌍 Set Timezone"
   - Send `America/New_York`

6. **Test fast schedule (for testing daily reminders):**
   - Set `DEBUG_FAST_SCHEDULE=1` in `.env`
   - Restart bot
   - Add an exam with future date
   - Wait 60 seconds - should receive notification

### Command Testing

Test commands directly:
```
/add Final Exam | 2026-02-01 14:00
/list
/settime 08:00
/timezone Europe/London
/delete 1
```

## Project Structure

```
exam_countdown_bot/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py          # Entry point, bot initialization
│   ├── config.py        # Configuration and environment variables
│   ├── db.py            # Database operations
│   ├── scheduler.py     # JobQueue scheduling logic
│   ├── handlers.py      # Command and callback handlers
│   ├── keyboards.py     # Reply and inline keyboard definitions
│   ├── conversations.py # ConversationHandler for Add Exam flow
│   └── utils.py         # Utility functions (date parsing, etc.)
```

## Database Schema

**users table:**
- `user_id` (INTEGER PRIMARY KEY) - Telegram user ID
- `timezone` (TEXT) - IANA timezone (default: 'Europe/Rome')
- `notify_time` (TEXT) - Daily notification time HH:MM (default: '09:00')

**exams table:**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `user_id` (INTEGER) - Foreign key to users
- `title` (TEXT) - Exam title
- `exam_datetime_iso` (TEXT) - ISO format datetime

## Troubleshooting

**Bot doesn't respond:**
- Check if BOT_TOKEN is correct in `.env`
- Ensure bot is not running elsewhere
- Check firewall/antivirus settings

**Notifications not working:**
- Verify timezone is correct: `/timezone Europe/Rome`
- Check notification time: `/settime 09:00`
- For testing, use DEBUG_FAST_SCHEDULE=1

**Database errors:**
- Delete `exam_bot.db` file and restart (will lose data)

## Deployment

### Local Development
See installation instructions above.

### Heroku Deployment
For deploying to Heroku (free tier available), see detailed guide:
👉 **[HEROKU_DEPLOY.md](HEROKU_DEPLOY.md)** (راهنمای فارسی)

Quick Heroku deploy:
```bash
heroku login
heroku create
heroku config:set BOT_TOKEN=your_token_here
git push heroku master
heroku ps:scale worker=1
heroku logs --tail
```

### Other Platforms
- **Railway.app** - Similar to Heroku
- **Render.com** - Free tier available
- **Fly.io** - Free tier available
- **VPS** - Any Linux server with Python 3.11+

## License

MIT License - Free to use and modify

## Support

Created with Python 3.11+ and python-telegram-bot library.
