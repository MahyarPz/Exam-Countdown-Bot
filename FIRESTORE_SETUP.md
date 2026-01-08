# Google Firestore Setup Guide

This guide will help you set up Google Cloud Firestore as your database for the Exam Countdown Bot.

## Why Firestore?

- ☁️ Cloud-based (no local database)
- 🔄 Real-time synchronization
- 🌍 Global distribution
- 💰 Free tier (up to 50,000 reads/day)
- 📱 Great for Heroku deployments

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Create a project"
3. Enter project name (e.g., "exam-countdown-bot")
4. Disable Google Analytics (optional)
5. Click "Create project"
6. Wait for project to be ready
7. **Copy your Project ID** - you'll need this later

## Step 2: Set Up Firestore Database

1. In Firebase Console, go to **Build** → **Firestore Database**
2. Click **Create Database**
3. Choose region (closest to you):
   - US: `us-central1` (default)
   - Europe: `europe-west1`
4. Start in **Production mode** (we'll set rules next)
5. Click **Create**

## Step 3: Set Up Security Rules

1. Go to **Firestore Database** → **Rules** tab
2. Replace the rules with:

```firestore
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write by owner only
    match /users/{userId} {
      allow read, write: if request.auth.uid == userId;
      
      // User's exams collection
      match /exams/{examId} {
        allow read, write: if request.auth.uid == userId;
      }
    }
    
    // Allow service account full access
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

3. Click **Publish**

## Step 4: Create Service Account

1. Go to **Project Settings** (gear icon) → **Service Accounts**
2. Click **Generate New Private Key**
3. Click **Generate Key**
4. A JSON file will download (e.g., `exam-countdown-bot-xxx.json`)
5. **Keep this file safe** - it contains your credentials

## Step 5: Set Up Locally

### Option A: Using JSON File Path

```bash
# Create .env file
cp .env.example .env

# Edit .env:
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_id
USE_FIRESTORE=1
FIREBASE_PROJECT_ID=exam-countdown-bot  # Your project ID
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-key.json
```

### Option B: Using JSON String (for Heroku)

```bash
# Use the setup script
python setup_firestore.py firebase-key.json
```

This will output a single-line JSON string. Copy it.

## Step 6: Deploy to Heroku

### Using Heroku Dashboard

1. Go to your Heroku app → **Settings**
2. Click **Reveal Config Vars**
3. Add these variables:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Your bot token from BotFather |
| `ADMIN_ID` | Your Telegram user ID |
| `USE_FIRESTORE` | `1` |
| `FIREBASE_PROJECT_ID` | Your Firebase project ID |
| `FIREBASE_CREDENTIALS` | Paste the JSON string from setup_firestore.py output |

### Using Heroku CLI

```bash
heroku config:set BOT_TOKEN=your_token --app your-app-name
heroku config:set ADMIN_ID=your_id --app your-app-name
heroku config:set USE_FIRESTORE=1 --app your-app-name
heroku config:set FIREBASE_PROJECT_ID=exam-countdown-bot --app your-app-name
heroku config:set 'FIREBASE_CREDENTIALS={"type":"service_account",...}' --app your-app-name
```

## Step 7: Verify Setup

1. Check Heroku logs:
```bash
heroku logs --tail --app your-app-name
```

2. Look for message:
```
Firestore initialized successfully
```

3. Test the bot with `/start` command

## Step 8: Monitor Firestore

1. Go to Firebase Console → **Firestore Database**
2. You should see collections appearing:
   - `users/` - one document per user ID
   - `users/{userId}/exams/` - exams for each user

## Troubleshooting

### Error: "Firebase credentials not found"
- Make sure `FIREBASE_CREDENTIALS` or `GOOGLE_APPLICATION_CREDENTIALS` is set
- If using JSON string, make sure it's valid JSON

### Error: "Invalid Firebase project ID"
- Check that `FIREBASE_PROJECT_ID` matches your Firebase project ID
- Project ID is in Firebase Console → Project Settings

### Database is empty
- Firestore is working fine - it starts empty
- Data will be added when users interact with bot
- Add an exam with bot to test

### High costs
- Check Firestore pricing dashboard in Firebase Console
- Free tier: 50,000 reads/day, 20,000 writes/day
- Typical bot usage: ~100 reads/day, 10 writes/day

## Migrating From SQLite

If you have data in SQLite, you'll need to migrate it manually:

1. Export your SQLite data to JSON
2. Write a migration script or import manually to Firestore
3. Contact the development team for migration help

## Security Notes

⚠️ **Important:**
- Never commit `firebase-key.json` to git
- Add to `.gitignore`:
  ```
  firebase-key.json
  ```
- Rotate your credentials periodically
- Use Firestore rules to protect user data

## References

- [Firebase Console](https://console.firebase.google.com)
- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Firebase Security Rules](https://firebase.google.com/docs/firestore/security/start)
