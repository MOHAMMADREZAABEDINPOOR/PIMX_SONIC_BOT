<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=1,12,24,30&height=220&section=header&text=PIMX_SONIC_BOT&fontSize=40&fontAlignY=35&desc=%F0%9F%9B%91%20Archived%20Open-Source%20Music%20Extraction%20Daemon&descFontSize=16&descAlignY=62" alt="PIMX_SONIC_BOT Banner" width="100%" />

<a href="https://github.com/MOHAMMADREZAABEDINPOOR/PIMX_SONIC_BOT">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=20&duration=2800&pause=1000&color=00D2FF&center=true&vCenter=true&width=780&lines=Project+Status%3A+Inactive+%2F+Archived+Media+Extraction+Daemon;High-Speed+Multi-Source+Audio+Downloader+(YouTube%2C+SoundCloud%2C+Spotify);Automated+yt-dlp+Extraction+with+FFmpeg+320kbps+MP3+Transcoding;Embedded+Album+Cover+Art%2C+ID3+Tags+%26+Metadata+Synchronization;Automated+Disk+Cleanup+Daemon+Purging+Temporary+Files+Post-Delivery;Asynchronous+Python+3.10%2B+Engine+Powered+by+python-telegram-bot+v20%2B;Bilingual+Interactive+Interface+with+Persian+(jdatetime)+Date+Tracking" alt="Typing SVG" />
</a>

<br/>

[![Project Status: Inactive / Archived](https://img.shields.io/badge/Status-Inactive%20%7C%20Archived-critical?style=for-the-badge&logo=archive)](https://github.com/MOHAMMADREZAABEDINPOOR)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg?style=for-the-badge&logo=gnu)](https://www.gnu.org/licenses/agpl-3.0)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![yt-dlp](https://img.shields.io/badge/Downloader-yt--dlp-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![Telegram Bot API](https://img.shields.io/badge/Telegram_Bot_API-v20+-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![SQLite](https://img.shields.io/badge/Database-SQLite3_WAL-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Read in Persian](https://img.shields.io/badge/مطالعه_به_فارسی-Persian_README-008080?style=for-the-badge)](#-بخش-فوقالعاده-مفصل-و-جامع-به-زبان-فارسی-persian-documentation)

<p align="center">
  <b>PIMX_SONIC_BOT</b> is a high-velocity Telegram audio and media extraction daemon built with Python 3.10+, <code>python-telegram-bot</code> v20+, and <code>yt-dlp</code>. Engineered for high-throughput music discovery, PIMX_SONIC_BOT extracts studio-quality 320kbps MP3 audio from YouTube, SoundCloud, and social links, embeds genuine ID3 metadata and high-res cover art, and automatically purges downloaded cache to maintain zero server disk bloat.
</p>

[Project Overview](#-project-overview) •
[Directory Anatomy](#-exhaustive-directory--file-anatomy) •
[Transcoding Pipeline](#-audio-transcoding--metadata-pipeline) •
[Quick Start](#-quick-start--installation) •
[توضیحات فارسی](#-بخش-فوقالعاده-مفصل-و-جامع-به-زبان-فارسی-persian-documentation) •
[License](#-copyleft-license--legal-attribution)

</div>

---

> [!CAUTION]
> ### 🛑 Project Status: Inactive / Archived (پروژه غیرفعال و بایگانی‌شده)
> **Notice**: This repository is currently **inactive** and preserved as an archived open-source audio extraction reference. The live Telegram bot is offline.
>
> **توجه مهم**: این پروژه در حال حاضر **کاملاً غیرفعال** است و سرور یا ربات فعالی روی آن اجرا نمی‌شود. این ریپازیتوری صرفاً به عنوان آرشیو فنی سورس‌کد حفظ گردیده است.

## ⚡ Project Overview

Searching for, downloading, and converting high-quality music files on mobile devices is often disrupted by paywalls, intrusive advertisements, and low-bitrate rips.

**PIMX_SONIC_BOT** streamlines music acquisition directly inside Telegram:
- 🎵 **Multi-Platform Audio Ingestion**: Accepts YouTube URLs, SoundCloud links, Spotify track shares, or plain-text song titles.
- ⚡ **Asynchronous Concurrency**: Built on `asyncio` and thread pools to process multiple concurrent music extraction requests simultaneously.
- 🧹 **Zero-Bloat Automated Garbage Collection**: Files are transmitted directly to the requesting Telegram chat and wiped from the host disk within 60 seconds.
- 🏷️ **Pristine ID3 Tagging**: Injects track title, artist name, album name, year, and thumbnail cover art directly into the MP3 container.

---

## 📂 Exhaustive Directory & File Anatomy

```
d:/code/PIMX_SONIC_BOT/
│
├── main2.py                         # 1800+ lines of asynchronous Telegram bot logic, yt-dlp & FFmpeg pipeline
├── main2.zip                        # Bundled distribution package for remote server deployments
├── requirements.txt                 # Dependencies (python-telegram-bot, yt-dlp, aiohttp, jdatetime)
├── users.db (Auto-created)          # SQLite user registry storing interactions, queries & download quotas
├── downloads/ (Ephemeral)           # Temporary scratch directory automatically purged post-transmission
└── README.md                        # Master comprehensive bilingual documentation
```

---

## 🚀 Quick Start & Installation

```bash
git clone https://github.com/MOHAMMADREZAABEDINPOOR/PIMX_SONIC_BOT.git
cd PIMX_SONIC_BOT

python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux:
source venv/bin/activate

pip install -r requirements.txt
python main2.py
```

---

## 🇮🇷 بخش فوق‌العاده مفصل و جامع به زبان فارسی (Persian Documentation)

### ۱. معرفی ربات دانلود موسیقی PIMX_SONIC_BOT
ربات **PIMX_SONIC_BOT** یک دستیار هوشمند و فوق‌العاده پرسرعت در تلگرام برای جستجو، استخراج و دانلود قطعات موسیقی با بالاترین کیفیت ممکن (۳۲۰ کیلوبیت بر ثانیه) از یوتیوب، ساندکلاد و پلتفرم‌های پخش آنلاین است. این ربات با ترکیب فریم‌ورک ناهمگام **python-telegram-bot v20+** و کتابخانه قدرتمند **yt-dlp**، تجربه دانلود موزیک را به سریع‌ترین شکل ممکن تبدیل می‌کند.

---

### ۲. تشریح ساختار فایل‌های پروژه
- **`main2.py`**: بیش از ۱۸۰۰ سطر کد پایتون شامل صف دانلود ناهمگام، استخراج فایل صوتی، تزریق برچسب‌های متادیتا (کاور آهنگ، نام خواننده و آلبوم)، و سیستم پاکسازی خودکار حافظه پس از ارسال به کاربر.
- **`users.db`**: دیتابیس SQLite برای ذخیره آمار کاربران و زمان‌بندی تاریخ‌های شمسی با پکیج `jdatetime`.

---

## 📜 Copyleft License & Legal Attribution

Distributed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

---

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=1,12,24,30&height=120&section=footer" alt="Footer" width="100%" />
<sub>Architected by <a href="https://github.com/MOHAMMADREZAABEDINPOOR"><b>MOHAMMADREZA ABEDINPOOR</b></a>. If PIMX_SONIC_BOT powers your music library, consider giving a ⭐!</sub>
</div>
