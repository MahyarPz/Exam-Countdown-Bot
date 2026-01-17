# Security Guidelines

## 🔐 Secret Management

This project uses environment variables for all sensitive configuration. **NEVER** commit secrets to the repository.

### Required Secrets

| Secret | Description | Where to Set |
|--------|-------------|--------------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | `.env` (local) / GitHub Secrets / Heroku Config |
| `ADMIN_ID` | Telegram user ID for admin features | `.env` / GitHub Secrets |
| `DATABASE_URL` | PostgreSQL connection string | Heroku auto-sets this |
| `FIREBASE_CREDENTIALS` | Firebase service account JSON | GitHub Secrets |

### Local Development

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your actual values in `.env`:
   ```
   BOT_TOKEN=your_actual_token_here
   ADMIN_ID=your_telegram_id
   ```

3. **NEVER commit `.env`** - it's already in `.gitignore`

### GitHub Secrets (for CI/CD)

1. Go to: Repository → Settings → Secrets and variables → Actions
2. Add repository secrets:
   - `BOT_TOKEN`: Your Telegram bot token
   - `ADMIN_ID`: Your Telegram user ID

### Heroku Deployment

```bash
heroku config:set BOT_TOKEN=your_token_here
heroku config:set ADMIN_ID=your_telegram_id
```

## 🛡️ Pre-commit Hook

A pre-commit hook is installed to prevent accidental secret commits. It checks for:
- Telegram bot token patterns (`123456789:ABC...`)
- `.env` files
- Log files (which may contain tokens in HTTP requests)

If the hook blocks your commit, review and remove any secrets before trying again.

### Installing the Hook (if needed)

The hook should be automatically present at `.git/hooks/pre-commit`. If not:
```bash
# Copy from the template or create manually
chmod +x .git/hooks/pre-commit
```

## 🚨 If a Secret is Exposed

If you accidentally commit a secret:

1. **Immediately revoke the compromised credential**
   - For Telegram: Message @BotFather → `/revoke` → Select bot

2. **Remove from Git history** (not just the latest commit):
   ```bash
   pip install git-filter-repo
   git filter-repo --invert-paths --path <file-with-secret>
   git push --force-with-lease origin main
   ```

3. **Generate a new credential** and update all deployments

4. **Notify affected parties** if user data could be at risk

## 📋 Files That Should NEVER Be Committed

- `.env` (local environment)
- `*.log` (may contain tokens in HTTP logs)
- `*.db`, `*.sqlite`, `*.sqlite3` (local databases)
- `firebase-credentials.json` or similar
- Any file containing API keys or tokens

All these are already in `.gitignore`.
