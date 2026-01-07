# Manual Testing Guide for Exam Countdown Bot

## Pre-requisites
1. Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram
2. Configure `.env` file with your BOT_TOKEN

## Quick Start Testing

### 1. Normal Mode (Daily Notifications)
```bash
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Edit .env and add your BOT_TOKEN

# Run bot
python -m app.main
```

### 2. Debug Mode (Fast Notifications - 60 seconds)
```bash
# Edit .env and add:
# DEBUG_FAST_SCHEDULE=1

# Run bot
python -m app.main
```

---

## Test Scenarios

### Test 1: Initial Setup & Start
**Steps:**
1. Start bot: Send `/start` in Telegram
2. **Expected:** Welcome message appears
3. **Expected:** Reply Keyboard menu appears with 6 buttons:
   - ➕ Add Exam
   - 📋 List Exams
   - 🗑 Delete Exam
   - ⏰ Set Daily Time
   - 🌍 Set Timezone
   - ℹ️ Help

**Verify:** All buttons are visible at bottom of chat

---

### Test 2: Add Exam via Button (Conversation Flow)
**Steps:**
1. Tap **"➕ Add Exam"** button
2. Bot asks: "What's the exam title?"
3. Send: `Mathematics Final`
4. Bot asks: "When is the exam?"
5. Send: `2026-01-25`
6. **Expected:** Confirmation message:
   ```
   ✅ Exam added successfully!
   📚 Mathematics Final
   📅 2026-01-25 09:00
   🆔 ID: 1
   ```
7. **Expected:** Main menu keyboard returns

**Verify:** Exam is saved with ID

---

### Test 3: Add Exam with Time
**Steps:**
1. Tap **"➕ Add Exam"**
2. Send: `Physics Exam`
3. Send: `2026-02-10 14:30`
4. **Expected:** Confirmation with time `14:30`

**Verify:** Time is correctly saved

---

### Test 4: Add Exam via Command
**Steps:**
1. Send: `/add Chemistry Test | 2026-03-05 10:00`
2. **Expected:** Exam added confirmation

**Verify:** Command-based add works

---

### Test 5: List Exams with Inline Buttons
**Steps:**
1. Tap **"📋 List Exams"** button
2. **Expected:** Message shows all exams with:
   - Exam ID
   - Title
   - Date/time
   - Countdown (e.g., "18 days left")
3. **Expected:** Inline buttons at bottom:
   - 🔄 Refresh
   - 🔔 Notify Now

**Verify:** All exams displayed correctly

---

### Test 6: Refresh Button
**Steps:**
1. After listing exams, tap **"🔄 Refresh"**
2. **Expected:** Message updates in place (edits existing message)
3. **Expected:** Countdown updates

**Verify:** No new message, existing one edited

---

### Test 7: Notify Now Button
**Steps:**
1. After listing exams, tap **"🔔 Notify Now"**
2. **Expected:** Bot answers callback: "Sending notification..."
3. **Expected:** New message appears:
   ```
   📚 Exam reminder:
   - Mathematics Final — 18 days left
   - Physics Exam — 33 days left
   - Chemistry Test — 55 days left
   ```

**Verify:** 
- Only upcoming exams shown
- Format matches daily reminder format
- Past exams not included

---

### Test 8: Delete Exam via Button
**Steps:**
1. Tap **"🗑 Delete Exam"** button
2. **Expected:** Message shows list with inline delete buttons:
   - 🗑 Delete #1 - Mathematics Final
   - 🗑 Delete #2 - Physics Exam
   - etc.
3. Tap **"🗑 Delete #1 - Mathematics Final"**
4. **Expected:** Message updates showing:
   - "✅ Exam deleted!"
   - Remaining exams
   - Delete buttons for remaining exams

**Verify:** 
- Exam removed from database
- List refreshes automatically
- Callback answer appears: "Exam #1 deleted!"

---

### Test 9: Delete via Command
**Steps:**
1. Send: `/list` to see IDs
2. Send: `/delete 2`
3. **Expected:** "✅ Exam #2 deleted successfully!"

**Verify:** Exam removed

---

### Test 10: Set Daily Notification Time
**Steps:**
1. Tap **"⏰ Set Daily Time"** button
2. Bot asks for time
3. Send: `08:30`
4. **Expected:** "✅ Daily notification time set to 08:30!"

**Alternative via command:**
- Send: `/settime 08:30`

**Verify:** Time saved and job rescheduled

---

### Test 11: Set Timezone
**Steps:**
1. Tap **"🌍 Set Timezone"** button
2. Bot asks for timezone
3. Send: `America/New_York`
4. **Expected:** "✅ Timezone set to America/New_York!"

**Alternative via command:**
- Send: `/timezone America/New_York`

**Verify:** Timezone saved and job rescheduled

---

### Test 12: Help Button
**Steps:**
1. Tap **"ℹ️ Help"** button
2. **Expected:** Help message with:
   - Menu button descriptions
   - Command list
   - Date format examples

**Alternative:** Send `/help`

**Verify:** Complete help displayed

---

### Test 13: Menu Command
**Steps:**
1. Send: `/menu`
2. **Expected:** Reply Keyboard menu appears

**Verify:** Can restore menu if hidden

---

### Test 14: Cancel Add Exam Flow
**Steps:**
1. Tap **"➕ Add Exam"**
2. Bot asks for title
3. Tap **"❌ Cancel"** button (appears in keyboard)
4. **Expected:** "❌ Cancelled adding exam."
5. **Expected:** Main menu returns

**Verify:** Conversation cancelled cleanly

---

### Test 15: Invalid Date Format
**Steps:**
1. Tap **"➕ Add Exam"**
2. Send: `Test Exam`
3. Send: `invalid-date`
4. **Expected:** Error message with correct format examples
5. **Expected:** Bot waits for valid date

**Verify:** Error handling works

---

### Test 16: Invalid Time Format
**Steps:**
1. Tap **"⏰ Set Daily Time"**
2. Send: `25:99`
3. **Expected:** Error message
4. Send: `09:00`
5. **Expected:** Success

**Verify:** Validation works

---

### Test 17: Invalid Timezone
**Steps:**
1. Tap **"🌍 Set Timezone"**
2. Send: `Invalid/Timezone`
3. **Expected:** Error with examples
4. Send: `Europe/Rome`
5. **Expected:** Success

**Verify:** Timezone validation works

---

### Test 18: Fast Schedule Testing (DEBUG MODE)
**Pre-requisite:** Set `DEBUG_FAST_SCHEDULE=1` in `.env` and restart bot

**Steps:**
1. Start bot (shows warning about DEBUG MODE)
2. Add an exam with future date: `/add Test | 2026-06-15`
3. Wait 60 seconds
4. **Expected:** Notification appears automatically
5. Wait another 60 seconds
6. **Expected:** Another notification

**Verify:** 
- Notifications sent every 60 seconds (not daily)
- Warning shown at startup
- Only upcoming exams included

---

### Test 19: Multiple Exams in Notification
**Steps:**
1. Add 3 exams with different dates:
   - `/add Exam A | 2026-01-20`
   - `/add Exam B | 2026-02-15`
   - `/add Exam C | 2026-03-10`
2. Tap "📋 List Exams"
3. Tap "🔔 Notify Now"
4. **Expected:** All 3 exams in one message, sorted by date

**Verify:** Multiple exams displayed correctly

---

### Test 20: No Upcoming Exams
**Steps:**
1. Delete all exams
2. Add past exam: `/add Past | 2020-01-01`
3. Tap "📋 List Exams" → Tap "🔔 Notify Now"
4. **Expected:** "ℹ️ You have no upcoming exams."

**Verify:** No notification for past exams

---

### Test 21: Same Day Exam
**Steps:**
1. Add exam for today: `/add Today Exam | 2026-01-07`
   (Use current date)
2. Tap "📋 List Exams"
3. **Expected:** Countdown shows "today"
4. Tap "🔔 Notify Now"
5. **Expected:** "Today Exam — today" in notification

**Verify:** "today" label appears correctly

---

### Test 22: List Empty Exams
**Steps:**
1. Ensure no exams exist
2. Tap **"📋 List Exams"**
3. **Expected:** "📋 You have no exams yet. Use ➕ Add Exam..."

**Verify:** Helpful message shown

---

### Test 23: Delete Non-existent Exam
**Steps:**
1. Send: `/delete 999`
2. **Expected:** "⚠️ Exam #999 not found or doesn't belong to you."

**Verify:** Error handling for invalid ID

---

### Test 24: Command Error Handling
**Steps:**
1. Send: `/add` (no arguments)
2. **Expected:** Usage instructions
3. Send: `/delete` (no arguments)
4. **Expected:** Usage instructions
5. Send: `/settime` (no arguments)
6. **Expected:** Usage instructions

**Verify:** All commands show help when arguments missing

---

### Test 25: Persistence Across Restarts
**Steps:**
1. Add 2 exams
2. Set time to 10:00
3. Set timezone to Asia/Tokyo
4. Stop bot (Ctrl+C)
5. Start bot again: `python -m app.main`
6. Send `/list`
7. **Expected:** All exams still present
8. Check logs for job scheduling confirmation

**Verify:** 
- Data persists in SQLite
- Jobs rescheduled on startup

---

## Quick Command Reference for Testing

```bash
# Start fresh (delete database)
del exam_bot.db
python -m app.main

# Commands to test
/start
/add Math | 2026-01-20 09:00
/add Physics | 2026-02-15 14:00
/list
/delete 1
/settime 09:00
/timezone Europe/Rome
/help
/menu
```

---

## Expected File Structure After Running

```
exam_countdown_bot/
├── exam_bot.db          # SQLite database (created on first run)
├── bot.log              # Log file (created on first run)
├── .env                 # Your config (created from .env.example)
└── [all project files]
```

---

## Common Issues & Solutions

**Issue:** Bot doesn't respond
- **Fix:** Check BOT_TOKEN in `.env` is correct
- **Fix:** Ensure bot is not running elsewhere

**Issue:** No notifications received
- **Fix:** Add at least one exam
- **Fix:** For testing, use DEBUG_FAST_SCHEDULE=1
- **Fix:** Check timezone is correct

**Issue:** "BOT_TOKEN environment variable is required"
- **Fix:** Create `.env` file from `.env.example`
- **Fix:** Add your token: `BOT_TOKEN=123456:ABC...`

**Issue:** Can't find python-telegram-bot
- **Fix:** Run `pip install -r requirements.txt`

---

## Success Criteria

✅ All 6 menu buttons work
✅ Add exam conversation flow completes
✅ Inline buttons (Refresh, Notify Now, Delete) work
✅ Delete exam via inline button works
✅ Daily time and timezone can be set
✅ Notifications format correctly
✅ Fast schedule works in debug mode
✅ Data persists across restarts
✅ Error handling works for invalid inputs
✅ Help and documentation accessible

---

**Testing Complete!** 🎉

If all tests pass, your bot is production-ready!
