# PIMX SONIC BOT ⚡🎵🤖

A high-speed Telegram music/media bot built for searching tracks, selecting quality/format, downloading with `yt-dlp`, and delivering files with automatic cleanup.

## What This Bot Does 🔥
- Searches music (especially SoundCloud-style results) with pagination
- Offers quality presets: `128kbps`, `320kbps`, and original quality
- Lets users choose output format (`MP3`, `M4A`, `MP4` where applicable)
- Downloads and sends media directly in Telegram
- Tracks users and usage data in SQLite
- Applies required channel membership gating
- Provides admin tools for stats and paginated user lists
- Removes downloaded files automatically after a delay

## Core Features 🎛️
- Inline/reply keyboard-based interactive UI
- Incremental result loading (`load more` behavior)
- Per-user state management via `context.user_data`
- Background cleanup worker thread for temp files
- Minimal-noise logging setup

## Commands & Actions 📌
- `/start` start panel and onboarding
- `/search <query>` search tracks
- `/stats` admin user statistics
- `/users` admin paginated user list
- Inline actions for navigation, quality, format, and back flow

## Data Layer 🗃️
- `users.db` (`sqlite3`) for user records and analytics-related data
- `downloads/` for temporary generated media
- Background delete queue clears files after send delay

## Tech Stack 🛠️
- Python
- `python-telegram-bot`
- `yt-dlp`
- `aiohttp`
- `sqlite3`
- `asyncio` + `threading`

## Configuration ⚙️
Current runtime constants in `main2.py`:
- `TOKEN`
- `ADMIN_ID`
- `DOWNLOAD_PATH`
- `DB_PATH`
- `REQUIRED_CHANNEL` / `REQUIRED_CHANNEL_LINK`
- `ITEMS_PER_PAGE`

Recommended production setup:
- Move secrets and identifiers to environment variables
- Isolate download/temp directories
- Add log rotation for long-running deployment

## Local Run 🚀
```bash
pip install -r requirements.txt
python main2.py
```

## Repository Structure 📂
- `main2.py`: main bot implementation
- `requirements.txt`: dependencies
- `users.db`: user database (runtime)
- `downloads/`: temporary output directory

## Reliability & Performance 🚦
- Async handlers keep Telegram interactions responsive
- Threaded cleaner prevents storage growth
- Paginated rendering avoids oversized message payloads

## Security Notes 🔐
- Never publish real Telegram bot tokens
- Rotate credentials if exposed
- Keep admin ID strict and membership checks enabled

## Project Goal 🎯
Deliver a fast, practical, and scalable Telegram music/media experience with clear UX and stable operational behavior.

<details>
<summary><strong>🇮🇷 نمایش توضیحات فارسی (ترجمه دقیق)</strong></summary>

# ربات PIMX SONIC ⚡🎵🤖

یک ربات پرسرعت موزیک/رسانه تلگرامی که برای جستجوی ترک، انتخاب کیفیت/فرمت، دانلود با `yt-dlp` و ارسال فایل همراه با پاک‌سازی خودکار ساخته شده است.

## این بات چه کار می‌کند 🔥
- جستجوی موزیک (به‌خصوص نتایج سبک SoundCloud) همراه با صفحه‌بندی
- ارائه کیفیت‌های `128kbps`، `320kbps` و کیفیت اصلی
- امکان انتخاب فرمت خروجی (`MP3`، `M4A` و در صورت امکان `MP4`)
- دانلود و ارسال مستقیم رسانه در تلگرام
- رهگیری کاربران و داده‌های مصرف در SQLite
- اعمال شرط عضویت کانال
- ابزارهای ادمین برای آمار و لیست صفحه‌بندی‌شده کاربران
- حذف خودکار فایل‌های دانلودشده بعد از یک تاخیر مشخص

## قابلیت‌های اصلی 🎛️
- رابط تعاملی مبتنی بر کیبورد inline/reply
- بارگذاری مرحله‌ای نتایج (`load more`)
- مدیریت وضعیت هر کاربر با `context.user_data`
- ترد پس‌زمینه برای پاک‌سازی فایل‌های موقت
- تنظیمات لاگ کم‌نویز

## دستورات و اکشن‌ها 📌
- `/start` پنل شروع و ورود کاربر
- `/search <query>` جستجوی موزیک
- `/stats` آمار کاربران برای ادمین
- `/users` لیست صفحه‌بندی‌شده کاربران برای ادمین
- اکشن‌های inline برای ناوبری، کیفیت، فرمت و بازگشت

## لایه داده 🗃️
- `users.db` با `sqlite3` برای رکورد کاربران و داده‌های مرتبط با آمار
- `downloads/` برای رسانه‌های موقت
- صف حذف پس‌زمینه برای پاک‌سازی فایل‌ها بعد از ارسال

## پشته فنی 🛠️
- Python
- `python-telegram-bot`
- `yt-dlp`
- `aiohttp`
- `sqlite3`
- `asyncio` + `threading`

## تنظیمات ⚙️
ثابت‌های اجرایی فعلاً در `main2.py`:
- `TOKEN`
- `ADMIN_ID`
- `DOWNLOAD_PATH`
- `DB_PATH`
- `REQUIRED_CHANNEL` / `REQUIRED_CHANNEL_LINK`
- `ITEMS_PER_PAGE`

پیشنهاد برای محیط پروداکشن:
- انتقال مقادیر محرمانه و شناسه‌ها به متغیر محیطی
- ایزوله‌سازی مسیر دانلود/فایل موقت
- افزودن log rotation برای اجرای بلندمدت

## اجرای محلی 🚀
```bash
pip install -r requirements.txt
python main2.py
```

## ساختار ریپو 📂
- `main2.py`: پیاده‌سازی اصلی بات
- `requirements.txt`: وابستگی‌ها
- `users.db`: دیتابیس کاربران (زمان اجرا)
- `downloads/`: مسیر خروجی موقت

## پایداری و کارایی 🚦
- هندلرهای async برای پاسخ‌گویی بهتر در تعاملات تلگرام
- پاک‌کننده thread-based برای جلوگیری از رشد فضای ذخیره‌سازی
- رندر صفحه‌بندی‌شده برای جلوگیری از پیام‌های بیش‌ازحد حجیم

## نکات امنیتی 🔐
- توکن واقعی تلگرام را عمومی منتشر نکنید
- در صورت افشا، سریع credential را rotate کنید
- شناسه ادمین را محدود نگه دارید و چک عضویت را فعال بگذارید

## هدف پروژه 🎯
ارائه یک تجربه سریع، کاربردی و مقیاس‌پذیر از موزیک/رسانه در تلگرام با UX شفاف و رفتار عملیاتی پایدار.

</details>
