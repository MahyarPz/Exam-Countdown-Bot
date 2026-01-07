# دیپلوی ربات روی Heroku

راهنمای کامل برای اجرای ربات تلگرام روی Heroku (رایگان تا 550 ساعت در ماه)

## پیش‌نیازها

1. حساب کاربری Heroku (رایگان): [https://signup.heroku.com/](https://signup.heroku.com/)
2. نصب Heroku CLI: [https://devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3. نصب Git: [https://git-scm.com/downloads](https://git-scm.com/downloads)
4. توکن ربات از [@BotFather](https://t.me/BotFather)

---

## مرحله ۱: نصب Heroku CLI

### ویندوز:
دانلود و نصب از [اینجا](https://devcenter.heroku.com/articles/heroku-cli)

بررسی نصب:
```powershell
heroku --version
```

---

## مرحله ۲: لاگین به Heroku

```powershell
heroku login
```

مرورگر باز می‌شود و باید لاگین کنید.

---

## مرحله ۳: آماده‌سازی پروژه

```powershell
cd d:\projects\bot

# اگر git ندارید، ایجاد کنید
git init
git add .
git commit -m "Initial commit"
```

---

## مرحله ۴: ایجاد اپلیکیشن Heroku

```powershell
# انتخاب یک نام یونیک (یا خالی بگذارید برای نام رندوم)
heroku create exam-countdown-bot-123

# یا بدون نام:
heroku create
```

Heroku یک URL می‌دهد مثل: `https://exam-countdown-bot-123.herokuapp.com`

---

## مرحله ۵: تنظیم متغیر محیطی (توکن ربات)

```powershell
# توکن خود را جایگزین کنید
heroku config:set BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# اختیاری: برای تست سریع (اعلان هر 60 ثانیه)
heroku config:set DEBUG_FAST_SCHEDULE=1
```

بررسی متغیرها:
```powershell
heroku config
```

---

## مرحله ۶: دیپلوی به Heroku

```powershell
git push heroku master
# یا اگر branch اصلی main است:
git push heroku main
```

منتظر بمانید تا بیلد تمام شود (۱-۲ دقیقه).

---

## مرحله ۷: روشن کردن Worker

Heroku به طور پیش‌فرض worker را خاموش می‌کند. باید روشن کنید:

```powershell
heroku ps:scale worker=1
```

بررسی وضعیت:
```powershell
heroku ps
```

باید ببینید:
```
=== worker (Free): python -m app.main (1)
worker.1: up 2026/01/07 12:34:56
```

---

## مرحله ۸: بررسی لاگ‌ها

```powershell
heroku logs --tail
```

باید ببینید:
```
Bot started successfully!
Database initialized
Scheduled reminders for X users
```

برای خروج: `Ctrl+C`

---

## مرحله ۹: تست ربات

1. به تلگرام بروید
2. ربات خود را پیدا کنید
3. `/start` را بزنید
4. باید منوی دکمه‌ها نشان داده شود ✅

---

## دستورات مفید Heroku

### مشاهده وضعیت
```powershell
heroku ps
```

### ری‌استارت ربات
```powershell
heroku restart
```

### خاموش کردن ربات (صرفه‌جویی در ساعات رایگان)
```powershell
heroku ps:scale worker=0
```

### روشن کردن دوباره
```powershell
heroku ps:scale worker=1
```

### مشاهده لاگ‌های اخیر
```powershell
heroku logs --tail
```

### تغییر توکن ربات
```powershell
heroku config:set BOT_TOKEN=توکن_جدید
heroku restart
```

### غیرفعال کردن DEBUG MODE
```powershell
heroku config:unset DEBUG_FAST_SCHEDULE
heroku restart
```

### باز کردن داشبورد Heroku
```powershell
heroku open
```

### باز کردن پنل تنظیمات
```powershell
heroku addons
```

---

## آپدیت کردن ربات

هر بار که کد را تغییر دادید:

```powershell
git add .
git commit -m "توضیح تغییرات"
git push heroku master
heroku restart
```

---

## پایگاه داده (مهم!)

⚠️ **هشدار**: Heroku هر 24 ساعت دیسک را پاک می‌کند (ephemeral filesystem).

برای ماندگاری داده‌ها، باید از **Heroku Postgres** استفاده کنید:

### اضافه کردن Postgres (رایگان)

```powershell
heroku addons:create heroku-postgresql:essential-0
```

سپس کد را برای استفاده از PostgreSQL به جای SQLite آپدیت کنید.

**یا راه حل ساده‌تر**: استفاده از SQLite و پذیرش اینکه داده‌ها هر روز ریست می‌شوند (برای تست).

---

## هزینه‌ها (رایگان)

✅ **رایگان تا 550 ساعت در ماه** (با credit card تایید شده: 1000 ساعت)
- 1 worker = حدود 18 روز در ماه رایگان
- برای 24/7: نیاز به credit card (بدون هزینه)

### فعال‌سازی 1000 ساعت رایگان:
1. [Heroku Billing](https://dashboard.heroku.com/account/billing)
2. اضافه کردن credit card
3. بدون هزینه! فقط برای تایید هویت

---

## عیب‌یابی

### ربات اجرا نمی‌شود
```powershell
# بررسی وضعیت
heroku ps

# اگر crashed است
heroku logs --tail
heroku restart
```

### خطای "Application error"
```powershell
# بررسی لاگ‌ها
heroku logs --tail

# معمولاً به خاطر:
# - توکن اشتباه
# - خطا در کد
# - وابستگی‌های نصب نشده
```

### ربات قطع می‌شود
- بررسی کنید worker روشن است: `heroku ps:scale worker=1`
- ساعات رایگان تمام شده (بررسی: [Dashboard](https://dashboard.heroku.com/))

### پیام "No web processes running"
این نرمال است! شما worker دارید نه web process.

---

## دستورات سریع (کپی و اجرا)

```powershell
# Setup اولیه
cd d:\projects\bot
git init
git add .
git commit -m "Initial commit"
heroku login
heroku create
heroku config:set BOT_TOKEN=توکن_خود_را_اینجا_بگذارید
git push heroku master
heroku ps:scale worker=1
heroku logs --tail

# بررسی
heroku ps
heroku config

# آپدیت بعدی
git add .
git commit -m "Update"
git push heroku master
heroku restart
```

---

## مانیتورینگ

### داشبورد Heroku
```powershell
heroku open
```

یا به [dashboard.heroku.com](https://dashboard.heroku.com) بروید.

### لاگ‌های زنده
```powershell
heroku logs --tail
```

### استفاده از ساعات
Dashboard → App → Resources → بخش Dynos

---

## جایگزین‌های Heroku (اگر محدودیت ساعت دارید)

1. **Railway.app** - 500 ساعت رایگان
2. **Render.com** - رایگان با محدودیت
3. **Fly.io** - رایگان تا 3 ماشین کوچک
4. **PythonAnywhere** - رایگان با محدودیت

---

## چک‌لیست نهایی

✅ Heroku CLI نصب شد  
✅ Git نصب شد  
✅ لاگین به Heroku  
✅ اپلیکیشن ایجاد شد  
✅ توکن ربات تنظیم شد (`heroku config:set BOT_TOKEN=...`)  
✅ کد push شد (`git push heroku master`)  
✅ Worker روشن شد (`heroku ps:scale worker=1`)  
✅ لاگ‌ها OK است (`heroku logs --tail`)  
✅ ربات در تلگرام پاسخ می‌دهد  

---

## موفق باشید! 🚀

اگر مشکلی داشتید، `heroku logs --tail` را چک کنید یا بپرسید!
