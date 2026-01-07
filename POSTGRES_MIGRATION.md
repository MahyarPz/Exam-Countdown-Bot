# مهاجرت به PostgreSQL روی Heroku

این ربات حالا از PostgreSQL روی Heroku پشتیبانی می‌کند! 🎉

---

## چرا PostgreSQL؟

✅ داده‌ها دائمی هستند (از بین نمی‌روند)  
✅ مناسب production  
✅ رایگان تا 1 GB روی Heroku  
✅ پشتیبانی از هزاران کاربر همزمان  

❌ SQLite روی Heroku: هر 24 ساعت پاک می‌شود

---

## دیپلوی با PostgreSQL (خودکار)

Heroku به طور خودکار `DATABASE_URL` را تنظیم می‌کند:

```powershell
# 1. اضافه کردن Postgres به app (رایگان)
heroku addons:create heroku-postgresql:essential-0

# 2. بررسی DATABASE_URL (خودکار تنظیم شده)
heroku config

# 3. دیپلوی کد جدید
git add .
git commit -m "Added PostgreSQL support"
git push heroku master

# 4. ری‌استارت
heroku restart

# 5. بررسی لاگ‌ها
heroku logs --tail
```

باید ببینید:
```
Using PostgreSQL database
Database initialized successfully
```

✅ **تمام!** ربات حالا از PostgreSQL استفاده می‌کند.

---

## تست Local با PostgreSQL (اختیاری)

اگر می‌خواهید local هم از PostgreSQL استفاده کنید:

### 1. نصب PostgreSQL
- **ویندوز**: [Download](https://www.postgresql.org/download/windows/)
- **نصب در طول setup**: username و password تنظیم کنید

### 2. ایجاد Database
```sql
-- در psql یا pgAdmin
CREATE DATABASE exam_bot;
```

### 3. تنظیم .env
```env
DATABASE_URL=postgresql://username:password@localhost/exam_bot
BOT_TOKEN=your_token_here
```

### 4. نصب psycopg2
```powershell
pip install -r requirements.txt
```

### 5. اجرای ربات
```powershell
python -m app.main
```

باید ببینید: `Using PostgreSQL database`

---

## بررسی Database روی Heroku

### از طریق CLI
```powershell
# اتصال به database
heroku pg:psql

# مشاهده جداول
\dt

# مشاهده کاربران
SELECT * FROM users;

# مشاهده امتحان‌ها
SELECT * FROM exams;

# خروج
\q
```

### از طریق Dashboard
```powershell
heroku addons:open heroku-postgresql
```

---

## دستورات مفید Database

### اطلاعات database
```powershell
heroku pg:info
```

### Backup گرفتن
```powershell
heroku pg:backups:capture
heroku pg:backups:download
```

### ری‌ست کردن database
```powershell
heroku pg:reset DATABASE
heroku restart
```

---

## Migration از SQLite به PostgreSQL

اگر داده‌های قدیمی در SQLite دارید:

### روش 1: Export/Import دستی
```python
# export_sqlite.py - اجرا در local
import sqlite3
import json

conn = sqlite3.connect('exam_bot.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Export users
cursor.execute("SELECT * FROM users")
users = [dict(row) for row in cursor.fetchall()]

# Export exams
cursor.execute("SELECT * FROM exams")
exams = [dict(row) for row in cursor.fetchall()]

with open('backup.json', 'w') as f:
    json.dump({'users': users, 'exams': exams}, f)

print("Exported to backup.json")
```

سپس import به PostgreSQL:
```python
# import_postgres.py - اجرا در local با DATABASE_URL
import json
import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

with open('backup.json', 'r') as f:
    data = json.load(f)

# Import users
for user in data['users']:
    cursor.execute(
        "INSERT INTO users (user_id, timezone, notify_time) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        (user['user_id'], user['timezone'], user['notify_time'])
    )

# Import exams
for exam in data['exams']:
    cursor.execute(
        "INSERT INTO exams (user_id, title, exam_datetime_iso) VALUES (%s, %s, %s)",
        (exam['user_id'], exam['title'], exam['exam_datetime_iso'])
    )

conn.commit()
print("Imported successfully")
```

---

## Troubleshooting

### خطا: "psycopg2 not installed"
```powershell
pip install psycopg2-binary
```

### خطا: "relation does not exist"
Database initialize نشده:
```powershell
heroku restart
heroku logs --tail
```

### خطا: "could not connect to server"
```powershell
# بررسی DATABASE_URL
heroku config:get DATABASE_URL

# اگر خالی است، اضافه کنید:
heroku addons:create heroku-postgresql:essential-0
```

### بررسی نوع Database در حال استفاده
```powershell
heroku logs --tail | findstr "Using"
```

باید ببینید: `Using PostgreSQL database`

---

## تفاوت‌های SQLite و PostgreSQL

| ویژگی | SQLite | PostgreSQL |
|------|--------|-----------|
| **Local** | ✅ عالی | ⚠️ نیاز به نصب |
| **Heroku** | ❌ پاک می‌شود | ✅ دائمی |
| **Concurrent Users** | محدود | نامحدود |
| **Production** | ❌ نه | ✅ بله |
| **Setup** | خودکار | نیاز به addon |

---

## هزینه PostgreSQL روی Heroku

**Plan: Essential-0** (قبلاً Hobby Dev)
- 💰 **رایگان**
- 📦 1 GB فضا
- 🔗 20 connection همزمان
- ⏰ بدون محدودیت زمانی

برای بیشتر از 1 GB:
- Essential-1: $5/ماه (10 GB)
- Premium: از $50/ماه

---

## بررسی استفاده

```powershell
# بررسی فضای استفاده شده
heroku pg:info

# مثال خروجی:
# Plan:        Essential 0
# Status:      Available
# Data Size:   8.0 MB / 1 GB (در حال استفاده)
# Tables:      2
# Rows:        150 (تقریبی)
```

---

## Auto-Backup (اختیاری)

برای backup خودکار روزانه:

```powershell
# فعال‌سازی auto-backup (نیاز به credit card)
heroku pg:backups:schedule DATABASE_URL --at '02:00 Asia/Tehran'

# مشاهده backup‌ها
heroku pg:backups
```

---

## مقایسه عملکرد

**SQLite:**
- 🐌 Disk I/O
- ❌ از بین رفتن داده‌ها

**PostgreSQL:**
- 🚀 سریع‌تر
- ✅ دائمی
- ✅ بهینه برای production

---

## تبریک! 🎉

ربات شما حالا آماده production است با:
✅ PostgreSQL پایدار  
✅ Heroku deployment  
✅ Backup خودکار (اختیاری)  
✅ مقیاس‌پذیر  

هر سوالی داشتید بپرسید! 🚀
