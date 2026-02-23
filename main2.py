# -*- coding: utf-8 -*-
import os
import re
import logging
import time
import asyncio
import subprocess
import sys
import platform
import urllib.request
import zipfile
import tarfile
import tempfile
import shutil
import json
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from yt_dlp import YoutubeDL
import threading
import queue
import aiohttp
import jdatetime

# تنظیمات اصلی
TOKEN = "8139985859:AAEHMOxr8yyyT0jdpN_GU-a5QHBp-lVDXko"
ADMIN_ID = 5675632554  # چت آیدی شما
DOWNLOAD_PATH = "downloads"
ITEMS_PER_PAGE = 10
DB_PATH = "users.db"
REQUIRED_CHANNEL = "@PIMX_PASS"
REQUIRED_CHANNEL_LINK = "https://t.me/PIMX_PASS"

# تنظیمات ویندوز برای asyncio
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ایجاد پوشه دانلود
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

# تنظیمات لاگ - ساده و تمیز
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('bot.log', mode='w', encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)

# غیرفعال کردن لاگ‌های اضافی
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('telegram').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

# صف برای حذف فایل‌ها بعد از 30 ثانیه
delete_queue = queue.Queue()

# سیستم حذف خودکار فایل‌ها
def cleanup_worker():
    """کارگر برای حذف فایل‌ها بعد از 30 ثانیه"""
    while True:
        try:
            file_path, delete_time = delete_queue.get()
            if time.time() >= delete_time:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"فایل حذف شد: {file_path}")
                    except:
                        pass
                delete_queue.task_done()
            else:
                delete_queue.put((file_path, delete_time))
                delete_queue.task_done()
                time.sleep(1)
        except:
            time.sleep(1)

# شروع کارگر حذف فایل‌ها
cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
cleanup_thread.start()

# === سیستم دیتابیس کاربران ===
def init_database():
    """ایجاد دیتابیس کاربران"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usage_count INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

def update_user(user_id, username, first_name, last_name):
    """بروزرسانی اطلاعات کاربر"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # بررسی وجود کاربر
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user:
        # کاربر وجود دارد، فقط last_seen و usage_count را آپدیت کن
        cursor.execute('''
            UPDATE users 
            SET last_seen = CURRENT_TIMESTAMP, 
                usage_count = usage_count + 1,
                username = ?,
                first_name = ?,
                last_name = ?
            WHERE user_id = ?
        ''', (username, first_name, last_name, user_id))
    else:
        # کاربر جدید
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen, usage_count)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
        ''', (user_id, username, first_name, last_name))
    
    conn.commit()
    conn.close()

def get_user_stats():
    """دریافت آمار کاربران"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # کل کاربران
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # امروز
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE DATE(last_seen) = DATE('now', 'localtime')
    ''')
    today = cursor.fetchone()[0]
    
    # 1 ساعت اخیر
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_seen >= datetime('now', 'localtime', '-1 hour')
    ''')
    last_1h = cursor.fetchone()[0]
    
    # 3 ساعت اخیر
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_seen >= datetime('now', 'localtime', '-3 hours')
    ''')
    last_3h = cursor.fetchone()[0]
    
    # 24 ساعت اخیر
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_seen >= datetime('now', 'localtime', '-24 hours')
    ''')
    last_24h = cursor.fetchone()[0]
    
    # 1 ماه اخیر
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_seen >= datetime('now', 'localtime', '-30 days')
    ''')
    last_30d = cursor.fetchone()[0]
    
    # 3 ماه اخیر
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_seen >= datetime('now', 'localtime', '-90 days')
    ''')
    last_90d = cursor.fetchone()[0]
    
    # 3 سال اخیر
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_seen >= datetime('now', 'localtime', '-1095 days')
    ''')
    last_3y = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total_users,
        'today': today,
        'last_1h': last_1h,
        'last_3h': last_3h,
        'last_24h': last_24h,
        'last_30d': last_30d,
        'last_90d': last_90d,
        'last_3y': last_3y
    }

def get_user_list(page=0, per_page=50):
    """دریافت لیست کاربران با صفحه‌بندی"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    offset = page * per_page
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, last_seen, usage_count
        FROM users 
        ORDER BY last_seen DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    
    users = cursor.fetchall()
    conn.close()
    
    return users

def get_total_users_count():
    """دریافت تعداد کل کاربران"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

# تابع برای حذف کدهای ANSI از رشته
def clean_ansi(text):
    """حذف کدهای رنگی ANSI از رشته"""
    if not text:
        return ""
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)

# تابع برای نصب FFmpeg
def install_ffmpeg():
    """نصب خودکار FFmpeg بر اساس سیستم عامل"""
    system = platform.system()
    
    print("🔍 بررسی FFmpeg...")
    
    # ابتدا بررسی کن ببین آیا از قبل نصب شده
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg از قبل نصب شده است")
            return True
    except:
        pass
    
    print("📥 در حال نصب FFmpeg...")
    
    try:
        if system == "Windows":
            # برای ویندوز - استفاده از لینک مستقیم و سریع
            ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "ffmpeg.zip")
            
            # دانلود FFmpeg
            print("در حال دانلود FFmpeg...")
            try:
                urllib.request.urlretrieve(ffmpeg_url, zip_path)
                print("✅ دانلود کامل شد")
            except Exception as e:
                print(f"❌ خطا در دانلود: {e}")
                return False
            
            # اکسترکت
            print("📦 در حال استخراج فایل‌ها...")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                print("✅ استخراج کامل شد")
            except:
                print("❌ خطا در استخراج فایل")
                return False
            
            # پیدا کردن پوشه ffmpeg
            ffmpeg_dir = None
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if os.path.isdir(item_path) and 'ffmpeg' in item.lower():
                    ffmpeg_dir = item_path
                    break
            
            if ffmpeg_dir:
                # پیدا کردن فایل‌های اجرایی
                bin_path = os.path.join(ffmpeg_dir, 'bin')
                if os.path.exists(bin_path):
                    target_dir = os.getcwd()
                    
                    # کپی فایل‌های اجرایی
                    for exe_file in ['ffmpeg.exe', 'ffprobe.exe']:
                        source_path = os.path.join(bin_path, exe_file)
                        if os.path.exists(source_path):
                            dest_path = os.path.join(target_dir, exe_file)
                            shutil.copy2(source_path, dest_path)
                            print(f"✅ {exe_file} کپی شد")
                    
                    # اضافه کردن مسیر به PATH برای این session
                    os.environ['PATH'] = target_dir + os.pathsep + os.environ['PATH']
                    
                    # تمیزکاری
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
                    
                    print("✅ FFmpeg با موفقیت نصب شد")
                    return True
                else:
                    print("❌ پوشه bin یافت نشد")
                    return False
            else:
                print("❌ پوشه ffmpeg یافت نشد")
                return False
                
        elif system == "Linux":
            # برای لینوکس
            print("🔄 تلاش برای نصب FFmpeg...")
            try:
                # ابتدا بررسی کن آیا apt-get موجود است
                result = subprocess.run(['which', 'apt-get'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("📦 استفاده از apt-get...")
                    subprocess.run(['apt-get', 'update'], capture_output=True)
                    subprocess.run(['apt-get', 'install', '-y', 'ffmpeg'], capture_output=True)
                else:
                    # بررسی yum
                    result = subprocess.run(['which', 'yum'], capture_output=True, text=True)
                    if result.returncode == 0:
                        print("📦 استفاده از yum...")
                        subprocess.run(['yum', 'install', '-y', 'ffmpeg'], capture_output=True)
                    else:
                        print("⚠️  مدیر بسته‌ی شناخته شده‌ای یافت نشد")
                        return False
                
                print("✅ FFmpeg با موفقیت نصب شد")
                return True
            except Exception as e:
                print(f"❌ خطا در نصب FFmpeg: {e}")
                return False
                
        elif system == "Darwin":  # macOS
            print("🍎 برای macOS، لطفاً دستی نصب کنید:")
            print("   brew install ffmpeg")
            return False
            
    except Exception as e:
        print(f"❌ خطا در نصب FFmpeg: {e}")
        return False

# کلاس برای مدیریت دانلود
class DownloadManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.current_progress_dict = {}
        self.last_logged_block = {}
        self.session = None
        
    async def get_session(self):
        """ایجاد session برای aiohttp"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
        
    def progress_hook(self, d, user_id):
        """هوک برای گرفتن پیشرفت از yt-dlp"""
        try:
            if d.get('status') == 'downloading':
                if user_id not in self.current_progress_dict:
                    self.current_progress_dict[user_id] = {
                        'progress': 0,
                        'speed': '',
                        'eta': '',
                        'last_update': time.time(),
                        'last_log_block': -1
                    }
                
                # گرفتن درصد و پاکسازی از کدهای ANSI
                percent_str = d.get('_percent_str', '0%')
                if percent_str:
                    # حذف کدهای رنگی ANSI
                    percent_str = clean_ansi(percent_str)
                    percent_str = percent_str.strip().replace('%', '').replace('NA', '0')
                    
                    try:
                        progress_val = float(percent_str)
                        
                        # ذخیره پیشرفت
                        data = self.current_progress_dict[user_id]
                        data['progress'] = progress_val
                        
                        # ثبت لاگ فقط هر 5 درصد
                        current_block = int(progress_val // 5)
                        last_logged = data.get('last_log_block', -1)
                        
                        if current_block > last_logged and current_block <= 20:
                            logger.info(f"پیشرفت: {progress_val:.1f}%")
                            data['last_log_block'] = current_block
                        
                        # ذخیره سرعت و زمان
                        speed_str = clean_ansi(d.get('_speed_str', '')).strip()
                        if speed_str:
                            data['speed'] = speed_str
                        
                        eta_str = clean_ansi(d.get('_eta_str', '')).strip()
                        if eta_str:
                            data['eta'] = eta_str
                        
                        data['last_update'] = time.time()
                        
                    except:
                        pass
                        
        except:
            pass
    
    def get_progress(self, user_id):
        """دریافت پیشرفت کاربر"""
        if user_id in self.current_progress_dict:
            data = self.current_progress_dict[user_id]
            if time.time() - data['last_update'] > 10:
                return 0, "", ""
            return data['progress'], data['speed'], data['eta']
        return 0, "", ""
    
    async def update_progress_in_bot(self, update, context, message_id, user_id, percentage, speed="", eta=""):
        """آپدیت درصد دانلود در بات برای کاربر"""
        try:
            text = "🎵 **در حال دانلود...**\n\n"
            
            # نوار پیشرفت
            bars = 20
            filled = int(bars * percentage / 100)
            progress_bar = "█" * filled + "░" * (bars - filled)
            
            # نمایش درصد با یک رقم اعشار
            text += f"📊 **پیشرفت:** `{percentage:.1f}%`\n"
            text += f"`[{progress_bar}]`\n"
            
            if speed and speed != 'N/A':
                text += f"⚡ **سرعت:** `{speed}`\n"
            if eta and eta != 'N/A':
                text += f"⏰ **زمان باقی‌مانده:** `{eta}`\n"
            
            if percentage == 0:
                text += "\n🔄 **در حال شروع دانلود...**"
            elif percentage >= 100:
                text = "✅ **دانلود کامل شد!**\n🚀 **در حال پردازش و ارسال فایل...**"
            
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=message_id,
                    text=text,
                    parse_mode='Markdown'
                )
                return True
            except:
                return False
                
        except:
            return False
    
    async def download_and_convert(self, url, title, format_choice='mp3', user_id=None):
        """دانلود و تبدیل به فرمت انتخابی"""
        try:
            safe_title = re.sub(r'[<>:"/\\|?*]', '', title)[:100]
            # جلوگیری از تداخل نام فایل‌ها (کاربران همزمان)
            unique_tag = f"{int(time.time())}_{user_id or 'u'}"
            base_name = f"{safe_title}_{unique_tag}"
            
            # مرحله 1: دانلود فایل اصلی
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{DOWNLOAD_PATH}/{base_name}.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'progress_hooks': [lambda d: self.progress_hook(d, user_id)],
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                'socket_timeout': 30,
                'retries': 3,
                'extract_audio': False,
                'prefer_ffmpeg': True,
                'no_color': True,
                'postprocessors': [],
            }
            
            # اگر فرمت MP3 است، extract_audio را فعال کن
            if format_choice.startswith('mp3'):
                ydl_opts['postprocessors'].append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                })
                if format_choice == 'mp3_128':
                    ydl_opts['postprocessors'][0]['preferredquality'] = '128'
                elif format_choice == 'mp3_320':
                    ydl_opts['postprocessors'][0]['preferredquality'] = '320'
            
            # استفاده از get_event_loop به جای get_running_loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            def download_task():
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    return filename, info
            
            # دانلود فایل اصلی
            filename, info = await loop.run_in_executor(self.executor, download_task)
            
            if not os.path.exists(filename):
                for file in os.listdir(DOWNLOAD_PATH):
                    if base_name in file:
                        filename = os.path.join(DOWNLOAD_PATH, file)
                        break
                else:
                    return None, "فایل دانلود شده یافت نشد"
            
            # بررسی وجود ffmpeg در مسیر جاری
            has_ffmpeg = False
            # اول در مسیر جاری بگرد
            if os.path.exists('ffmpeg.exe') or os.path.exists('ffmpeg'):
                has_ffmpeg = True
            else:
                # سپس در PATH بگرد
                try:
                    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        has_ffmpeg = True
                except:
                    pass
            
            # اگر فرمت M4A انتخاب شده و فایل هم m4a است
            if format_choice in ['m4a', 'aac'] and filename.endswith(('.m4a', '.aac')):
                return filename, "موفق"
            
            # اگر فرمت MP3 انتخاب شده
            output_filename = None
            if format_choice.startswith('mp3'):
                mp3_filename = filename.rsplit('.', 1)[0] + '.mp3'
                
                if has_ffmpeg:
                    if format_choice == 'mp3_128':
                        quality = '4'
                    elif format_choice == 'mp3_320':
                        quality = '0'
                    else:
                        quality = '2'
                    
                    # استفاده از ffmpeg در مسیر جاری اگر وجود دارد
                    ffmpeg_cmd = 'ffmpeg.exe' if os.path.exists('ffmpeg.exe') else 'ffmpeg'
                    
                    cmd = [
                        ffmpeg_cmd, '-i', filename,
                        '-codec:a', 'libmp3lame',
                        '-qscale:a', quality,
                        '-y', mp3_filename
                    ]
                    
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                        if result.returncode == 0 and os.path.exists(mp3_filename):
                            output_filename = mp3_filename
                            try:
                                os.remove(filename)
                            except:
                                pass
                    except:
                        pass
                else:
                    # اگر ffmpeg نیست، کپی با نام جدید
                    output_filename = mp3_filename
                    shutil.copy2(filename, output_filename)
            
            # اگر فرمت MP4 انتخاب شده
            elif format_choice == 'mp4':
                mp4_filename = filename.rsplit('.', 1)[0] + '.mp4'
                
                if has_ffmpeg:
                    ffmpeg_cmd = 'ffmpeg.exe' if os.path.exists('ffmpeg.exe') else 'ffmpeg'
                    
                    cmd = [
                        ffmpeg_cmd, '-i', filename,
                        '-c', 'copy',
                        '-y', mp4_filename
                    ]
                    
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                        if result.returncode == 0 and os.path.exists(mp4_filename):
                            output_filename = mp4_filename
                            try:
                                os.remove(filename)
                            except:
                                pass
                    except:
                        return None, "خطا در تبدیل به MP4"
                else:
                    return None, "برای تبدیل به MP4 نیاز به نصب FFmpeg است"
            else:
                output_filename = filename
            
            if not output_filename or not os.path.exists(output_filename):
                return None, "خطا در آماده‌سازی فایل خروجی"
            
            return output_filename, "موفق"
                
        except Exception as e:
            return None, str(e)

# ایجاد دانلود منیجر
download_manager = DownloadManager()

# --- تابع جستجو در SoundCloud ---
async def search_soundcloud(query: str, limit: int = 100, offset: int = 0):
    """جستجو در SoundCloud با yt-dlp"""
    results = []
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'default_search': 'scsearch',
        'force_generic_extractor': False,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            search_query = f"scsearch{limit}:{query}"
            info = ydl.extract_info(search_query, download=False)
            
            if info and 'entries' in info:
                entries = info['entries'][offset:offset+limit]
                
                for entry in entries:
                    if entry:
                        filesize = entry.get('filesize', entry.get('filesize_approx', 0))
                        if filesize:
                            size_mb = filesize / (1024 * 1024)
                        else:
                            duration = entry.get('duration', 180)
                            size_mb = (duration / 60) * 1.5
                        
                        track_info = {
                            'id': entry.get('id', ''),
                            'title': entry.get('title', 'بدون عنوان'),
                            'url': entry.get('url', ''),
                            'duration': entry.get('duration', 0),
                            'uploader': entry.get('uploader', 'ناشناس'),
                            'webpage_url': entry.get('webpage_url', entry.get('url', '')),
                            'estimated_size': round(size_mb, 1)
                        }
                        results.append(track_info)
    
    except Exception as e:
        logger.error(f"Search error: {e}")
    
    return results

# --- توابع کمکی ---
def format_duration(seconds):
    """تبدیل ثانیه به فرمت دقیقه:ثانیه"""
    try:
        if not seconds:
            return "0:00"
        
        seconds = int(seconds)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    except:
        return "0:00"

def clean_text(text, max_len=40):
    """تمیز کردن متن برای نمایش"""
    if not text:
        return "بدون عنوان"
    
    text = re.sub(r'[^\w\s\-\.\(\)\[\]\{\}آ-ی]', '', text)
    
    if len(text) > max_len:
        return text[:max_len-3] + "..."
    return text

def is_soundcloud_url(text: str) -> bool:
    """بررسی اینکه متن یک لینک SoundCloud است"""
    if not text:
        return False
    return bool(re.search(r'(https?://)?(www\.)?(soundcloud\.com|snd\.sc)/\S+', text, re.IGNORECASE))

async def handle_soundcloud_link(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """نمایش کیفیت/فرمت برای لینک SoundCloud مانند حالت جستجو"""
    status_message = await update.message.reply_text("⏳ در حال بررسی لینک...")
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extract_flat': False,
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        # اگر لینک پلی‌لیست بود
        if info and 'entries' in info:
            await status_message.edit_text("❌ این لینک پلی‌لیست است. لطفاً لینک یک آهنگ تکی بفرست.")
            return
        
        if not info:
            await status_message.edit_text("❌ اطلاعات آهنگ یافت نشد. لطفاً لینک را بررسی کنید.")
            return
        
        title = clean_text(info.get('title'))
        artist = clean_text(info.get('uploader') or info.get('artist'))
        duration = info.get('duration', 0)
        duration_str = format_duration(duration)

        filesize = info.get('filesize') or info.get('filesize_approx')
        if filesize:
            size_mb = round(filesize / (1024 * 1024), 1)
        else:
            size_mb = round((duration / 60) * 1.5, 1) if duration else 0

        track = {
            'id': info.get('id', ''),
            'title': info.get('title', ''),
            'url': info.get('url', url),
            'duration': duration,
            'uploader': info.get('uploader', 'ناشناس'),
            'webpage_url': info.get('webpage_url', url),
            'estimated_size': size_mb
        }
        context.user_data['selected_track'] = track

        info_text = f"""
🎵 **{title}**
👨‍🎤 **خواننده:** {artist}
⏱ **مدت زمان:** {duration_str}
💾 **حجم تخمینی:** {size_mb} MB

👇 **لطفاً کیفیت مورد نظر را انتخاب کنید:**
"""
        keyboard = [
            [InlineKeyboardButton("🎵 کیفیت 128kbps", callback_data="quality_128")],
            [InlineKeyboardButton("🔊 کیفیت 320kbps", callback_data="quality_320")],
            [InlineKeyboardButton("🎧 کیفیت اصلی", callback_data="quality_original")]
        ]

        await status_message.edit_text(
            text=info_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            error_msg = "❌ **خطا:** زمان عملیات به پایان رسید. لطفاً دوباره تلاش کنید."
        else:
            error_msg = f"❌ **خطا:** {error_msg[:150]}"
        await update.message.reply_text(error_msg, parse_mode='Markdown')

def get_file_size_mb(file_path):
    """محاسبه حجم فایل به مگابایت"""
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    return 0

def convert_to_jalali(timestamp):
    """تبدیل تاریخ میلادی به شمسی"""
    try:
        # اگر timestamp یک رشته است
        if isinstance(timestamp, str):
            # حذف . و بخش کسری
            if '.' in timestamp:
                timestamp = timestamp.split('.')[0]
            
            # تبدیل به datetime
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # تبدیل به تاریخ شمسی
        jalali = jdatetime.datetime.fromgregorian(datetime=dt)
        return jalali.strftime("%H:%M %Y-%m-%d")
    except:
        return "نامشخص"

def _chat_member_is_allowed(chat_member) -> bool:
    status = getattr(chat_member, "status", None)
    if status in ("member", "administrator", "creator"):
        return True
    if status == "restricted":
        return bool(getattr(chat_member, "is_member", False))
    return False

def _start_text() -> str:
    return """
🎵 **به ربات دانلود موزیک خوش آمدید!** 🎧

✅ **از همینجا شروع کن:**
• اگر دنبال آهنگ هستی، اسم آهنگ یا خواننده را بفرست.
• اگر لینک داری، لینک آهنگ SoundCloud را بفرست تا مستقیم دانلود شود.
• با دکمه‌های زیر هم می‌تونی سریع‌تر انتخاب کنی.

💡 **نکته:** برای بهترین نتیجه، نام کامل آهنگ/خواننده را وارد کن.
"""

def _help_text() -> str:
    return """
🎵 **به ربات دانلود موزیک خوش آمدید!** 🎧

✨ **ویژگی‌ها:**
• 🔍 جستجوی پیشرفته در SoundCloud
• 🎯 کیفیت‌های مختلف (MP3 128 / MP3 320 / M4A)
• ⚡ دانلود سریع + نمایش درصد

🎯 **روش‌های دانلود:**
• **جستجو:** اسم آهنگ یا خواننده را بفرستید.
• **لینک مستقیم:** لینک آهنگ SoundCloud را بفرستید تا دانلود شود.

🧭 **میانبرها (فقط برای ادمین):**
• دکمه «جستجوی موزیک» → نام آهنگ/خواننده را بنویسید.
• دکمه «دانلود موزیک» → لینک آهنگ را بفرستید.
• دکمه «راهنمای بات» → توضیحات کامل کارکرد ربات.
"""

def _inline_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 جستجوی موزیک", callback_data="ui_search"),
            InlineKeyboardButton("🎵 دانلود موزیک", callback_data="ui_link")
        ],
        [InlineKeyboardButton("ℹ️ راهنمای بات", callback_data="ui_help")]
    ])

def _inline_back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="ui_back")]])

def _admin_reply_keyboard():
    keyboard = [
        [KeyboardButton("📊 آمار کاربران"), KeyboardButton("📋 لیست کاربران")],
        [KeyboardButton("🔍 جستجوی موزیک"), KeyboardButton("🎵 دانلود موزیک")],
        [KeyboardButton("ℹ️ راهنمای بات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def _send_join_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, *, error_note: str | None = None):
    keyboard = [
        [InlineKeyboardButton("عضویت در کانال", url=REQUIRED_CHANNEL_LINK)],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "برای استفاده از ربات باید اول داخل کانال عضو بشی:\n"
        f"{REQUIRED_CHANNEL_LINK}\n\n"
        "بعد از عضویت روی «✅ عضو شدم» بزن."
    )
    if error_note:
        text += "\n\n" + f"اگر عضو هستی ولی تایید نمی‌شه، ربات باید داخل کانال ادمین باشه.\n({error_note})"

    if update.callback_query:
        try:
            await update.callback_query.answer()
        except:
            pass
        try:
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
            return
        except:
            pass

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
        return

    if update.effective_chat:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)

async def ensure_channel_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return True
    if user.id == ADMIN_ID:
        return True

    try:
        chat_member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user.id)
        if _chat_member_is_allowed(chat_member):
            return True
    except Exception as e:
        logger.info(f"Channel membership check failed for user_id={user.id}: {e}")
        await _send_join_prompt(update, context, error_note=str(e))
        return False

    await _send_join_prompt(update, context)
    return False

# --- هندلرهای ربات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع"""
    if not await ensure_channel_member(update, context):
        return

    user = update.effective_user
    user_id = user.id
    
    # ذخیره اطلاعات کاربر در دیتابیس
    update_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    start_text = _start_text()
    
    if user_id == ADMIN_ID:
        user_keyboard = [
            [KeyboardButton("📊 آمار کاربران"), KeyboardButton("📋 لیست کاربران")],
            [KeyboardButton("🔍 جستجوی موزیک"), KeyboardButton("🎵 دانلود موزیک")],
            [KeyboardButton("ℹ️ راهنمای بات")]
        ]
        reply_markup = ReplyKeyboardMarkup(user_keyboard, resize_keyboard=True)
        await update.message.reply_text(start_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        reply_markup = _inline_menu_keyboard()
        await update.message.reply_text(start_text, parse_mode='Markdown', reply_markup=reply_markup)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور آمار کاربران"""
    if not await ensure_channel_member(update, context):
        return

    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ این دستور فقط برای ادمین قابل دسترسی است.")
        return
    
    stats = get_user_stats()

    stats_text = (
        "📊 آمار کاربران\n"
        "────────────────\n"
        f"👥 کل کاربران: {stats['total']}\n"
        "────────────────\n"
        f"🗓️ امروز: {stats['today']}\n"
        f"⏱️ ۱ ساعت اخیر: {stats['last_1h']}\n"
        f"⏱️ ۳ ساعت اخیر: {stats['last_3h']}\n"
        f"🕘 ۲۴ ساعت اخیر: {stats['last_24h']}\n"
        f"🗓️ ۱ ماه اخیر: {stats['last_30d']}\n"
        f"🗓️ ۳ ماه اخیر: {stats['last_90d']}\n"
        f"🗓️ ۳ سال اخیر: {stats['last_3y']}\n"
    )

    await update.message.reply_text(stats_text)

async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور لیست کاربران"""
    if not await ensure_channel_member(update, context):
        return

    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ این دستور فقط برای ادمین قابل دسترسی است.")
        return
    
    # دریافت شماره صفحه از آرگومان‌ها
    page = 0
    if context.args:
        try:
            page = int(context.args[0]) - 1
            if page < 0:
                page = 0
        except:
            page = 0
    
    users = get_user_list(page=page, per_page=50)
    total_users = get_total_users_count()
    total_pages = (total_users + 49) // 50  # 50 کاربر در هر صفحه
    
    if not users:
        await update.message.reply_text("📭 هیچ کاربری یافت نشد.")
        return
    
    list_text = f"📋 لیست کاربران (صفحه {page + 1} از {total_pages})\n\n"
    
    for idx, user in enumerate(users, start=1):
        user_id, username, first_name, last_name, last_seen, usage_count = user
        
        # ساخت نام نمایشی
        display_name = ""
        if first_name:
            display_name += first_name
        if last_name:
            display_name += f" {last_name}"
        if not display_name.strip():
            display_name = "کاربر"
        
        # ساخت نام کاربری
        display_username = f"@{username}" if username else "@-"
        
        # تبدیل تاریخ آخرین فعالیت
        last_seen_jalali = convert_to_jalali(last_seen)
        
        list_text += f"👤 {display_name} | 🆔 {display_username} | 🔁 {usage_count} | 🕒 {last_seen_jalali}\n"
    
    # اضافه کردن دکمه‌های ناوبری
    keyboard = []
    nav_row = []
    
    if page > 0:
        nav_row.append(InlineKeyboardButton("⏪ صفحه قبلی", callback_data=f"users_page_{page-1}"))
    
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("صفحه بعدی ⏩", callback_data=f"users_page_{page+1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("📊 آمار کاربران", callback_data="users_stats")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(list_text, reply_markup=reply_markup)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور جستجو"""
    if not await ensure_channel_member(update, context):
        return

    if not context.args:
        help_text = """
🔍 **نحوه استفاده صحیح از جستجو:**

`/search [عبارت جستجو]`

📝 **مثال‌های کاربردی:**
`/search tataloo`
`/search علی زندونی`
`/search persian rap`

🎯 **همین الان تست کنید:**
`/search tataloo`
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    query = " ".join(context.args)
    
    search_msg = await update.message.reply_text(f"🔍 **در حال جستجوی '{query}'...**\n⏳ لطفاً کمی صبر کنید...", parse_mode='Markdown')
    
    results = await search_soundcloud(query, limit=100)
    
    if not results:
        await search_msg.edit_text(f"❌ **متأسفانه!**\nهیچ نتیجه‌ای برای '{query}' پیدا نشد.")
        return
    
    # ذخیره نتایج
    context.user_data['all_search_results'] = results
    context.user_data['current_page'] = 0
    context.user_data['search_query'] = query
    context.user_data['total_results'] = len(results)
    
    display_results = results[:100]
    context.user_data['display_results'] = display_results
    
    await show_results_page(update, context, search_msg)

async def show_results_page(update: Update, context: ContextTypes.DEFAULT_TYPE, message=None):
    """نمایش صفحه نتایج با دکمه‌های بزرگ"""
    all_results = context.user_data.get('all_search_results', [])
    display_results = context.user_data.get('display_results', all_results[:100])
    page = context.user_data.get('current_page', 0)
    query = context.user_data.get('search_query', '')
    total_results = context.user_data.get('total_results', 0)
    
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_results = display_results[start_idx:end_idx]
    
    if not page_results:
        if message:
            await message.edit_text("❌ خطا در نمایش نتایج")
        return
    
    total_pages = (len(display_results) - 1) // ITEMS_PER_PAGE + 1
    
    message_text = f"🔍 **نتایج جستجو:** `{query}`\n"
    message_text += f"📄 **صفحه {page + 1} از {total_pages}**\n"
    message_text += f"🎵 **تعداد کل:** {total_results} آهنگ\n\n"
    message_text += "👇 **برای دانلود روی آهنگ مورد نظر کلیک کنید:**\n"
    
    keyboard = []
    
    for idx, track in enumerate(page_results, start=1):
        global_idx = start_idx + idx
        
        title = clean_text(track['title'], 30)
        duration = format_duration(track['duration'])
        size_mb = track['estimated_size']
        
        button_text = f"🎵 {global_idx}. {title} | ⏱ {duration} | 💾 {size_mb}MB"
        callback_data = f"select_{start_idx + idx - 1}"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⏪ صفحه قبل", callback_data=f"prev_{page-1}"))
    
    if end_idx < len(display_results):
        nav_buttons.append(InlineKeyboardButton("صفحه بعد ⏩", callback_data=f"next_{page+1}"))
    else:
        if total_results > 100:
            current_offset = len(display_results)
            if current_offset < total_results:
                nav_buttons.append(
                    InlineKeyboardButton(f"🔽 بارگذاری ۵۰ آهنگ بعدی", callback_data=f"loadmore_{current_offset}")
                )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔍 جستجوی جدید", callback_data="new_search")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if message:
        await message.edit_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=message_text, 
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
        except:
            pass

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت کلیک روی دکمه‌ها"""
    query = update.callback_query
    data = query.data

    if data == "check_join":
        if await ensure_channel_member(update, context):
            try:
                await query.answer("✅ عضویت تایید شد")
            except:
                pass
            try:
                await query.message.reply_text(_help_text(), parse_mode="Markdown")
            except:
                pass
        return

    if data == "ui_search":
        await query.message.edit_text(
            "🔍 **اسم خواننده یا آهنگ رو بنویسید:**",
            parse_mode='Markdown',
            reply_markup=_inline_back_keyboard()
        )
        return
    if data == "ui_link":
        await query.message.edit_text(
            "🎵 **لینک آهنگ SoundCloud را بفرستید تا دانلود شود.**",
            parse_mode='Markdown',
            reply_markup=_inline_back_keyboard()
        )
        return
    if data == "ui_help":
        await query.message.edit_text(
            _help_text(),
            parse_mode="Markdown",
            reply_markup=_inline_back_keyboard()
        )
        return
    if data == "ui_back":
        await query.message.edit_text(
            _help_text(),
            parse_mode="Markdown",
            reply_markup=_inline_menu_keyboard()
        )
        return

    if not await ensure_channel_member(update, context):
        return

    try:
        await query.answer()
    except:
        pass
    
    # اگر دکمه مربوط به لیست کاربران است
    if data.startswith("users_page_"):
        page = int(data.split("_")[2])
        await list_users_page(update, context, page)
        return
    elif data == "users_stats":
        await show_user_stats(update, context)
        return
    
    if data.startswith("prev_") or data.startswith("next_"):
        action, page = data.split("_")
        context.user_data['current_page'] = int(page)
        await show_results_page(update, context)
    
    elif data.startswith("loadmore_"):
        offset = int(data.split("_")[1])
        search_query = context.user_data.get('search_query', '')
        
        await query.edit_message_text(f"🔄 **در حال بارگذاری نتایج بیشتر...**\n⏳ لطفاً منتظر بمانید...", parse_mode='Markdown')
        
        more_results = await search_soundcloud(search_query, limit=50, offset=offset)
        
        if more_results:
            current_results = context.user_data.get('all_search_results', [])
            current_results.extend(more_results)
            context.user_data['all_search_results'] = current_results
            
            new_display_results = current_results[:150]
            context.user_data['display_results'] = new_display_results
            context.user_data['total_results'] = len(current_results)
            
            context.user_data['current_page'] = 0
            
            await show_results_page(update, context)
        else:
            await query.edit_message_text(
                "❌ **هیچ نتیجه بیشتری یافت نشد!**",
                parse_mode='Markdown'
            )
    
    elif data.startswith("select_"):
        track_index = int(data.split("_")[1])
        display_results = context.user_data.get('display_results', [])
        
        if track_index >= len(display_results):
            await query.edit_message_text("❌ آهنگ پیدا نشد!")
            return
        
        track = display_results[track_index]
        context.user_data['selected_track'] = track
        
        title = clean_text(track['title'])
        artist = clean_text(track['uploader'])
        duration = format_duration(track['duration'])
        size_mb = track['estimated_size']
        
        info_text = f"""
🎵 **{title}**
👨‍🎤 **خواننده:** {artist}
⏱ **مدت زمان:** {duration}
💾 **حجم تخمینی:** {size_mb} MB

👇 **لطفاً کیفیت مورد نظر را انتخاب کنید:**
"""
        
        keyboard = [
            [InlineKeyboardButton("🎵 کیفیت 128kbps", callback_data="quality_128")],
            [InlineKeyboardButton("🔊 کیفیت 320kbps", callback_data="quality_320")],
            [InlineKeyboardButton("🎧 کیفیت اصلی", callback_data="quality_original")],
            [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="back_to_list")]
        ]
        
        await query.edit_message_text(
            text=info_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data.startswith("quality_"):
        quality = data.split("_")[1]
        track = context.user_data.get('selected_track')
        
        if not track:
            await query.edit_message_text("❌ خطا: اطلاعات آهنگ یافت نشد!")
            return
        
        title = clean_text(track['title'])
        artist = clean_text(track['uploader'])
        
        info_text = f"""
🎵 **{title}**
👨‍🎤 **خواننده:** {artist}

✅ **کیفیت انتخاب شده:** {quality}

👇 **لطفاً فرمت مورد نظر را انتخاب کنید:**
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🎵 MP3", callback_data=f"format_mp3_{quality}"),
                InlineKeyboardButton("🎧 M4A", callback_data=f"format_m4a_{quality}")
            ],
            [
                InlineKeyboardButton("🎬 MP4", callback_data=f"format_mp4_{quality}"),
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_quality")
            ]
        ]
        
        await query.edit_message_text(
            text=info_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data.startswith("format_"):
        parts = data.split("_")
        format_type = parts[1]
        quality = parts[2] if len(parts) > 2 else "original"
        
        track = context.user_data.get('selected_track')
        
        if not track:
            await query.edit_message_text("❌ خطا: اطلاعات آهنگ یافت نشد!")
            return
        
        title = clean_text(track['title'])
        artist = clean_text(track['uploader'])
        
        format_display = ""
        if format_type == "mp3":
            if quality == "128":
                format_choice = "mp3_128"
                format_display = "MP3 (128kbps)"
            elif quality == "320":
                format_choice = "mp3_320"
                format_display = "MP3 (320kbps)"
            else:
                format_choice = "mp3"
                format_display = "MP3 (192kbps)"
        elif format_type == "m4a":
            format_choice = "m4a"
            format_display = "M4A (کیفیت اصلی)"
        elif format_type == "mp4":
            format_choice = "mp4"
            format_display = "MP4 (فایل ویدیویی)"
        else:
            format_choice = "mp3"
            format_display = "MP3 (پیش‌فرض)"
        
        download_text = f"""
🎵 **آهنگ انتخاب شده:**
**{title}** - {artist}

📊 **فرمت:** {format_display}

⏳ **در حال آماده‌سازی دانلود...**
🔄 لطفاً منتظر بمانید
"""
        
        progress_message = await query.edit_message_text(
            text=download_text,
            parse_mode='Markdown'
        )
        
        try:
            track_url = track.get('webpage_url') or track.get('url')
            if not track_url:
                await query.message.reply_text("❌ لینک آهنگ پیدا نشد!")
                return
            
            async def update_progress(user_id, message_id):
                last_percentage = -1
                
                while True:
                    percentage, speed, eta = download_manager.get_progress(user_id)
                    
                    if percentage >= 100:
                        await download_manager.update_progress_in_bot(
                            update, 
                            context, 
                            message_id, 
                            user_id,
                            100, "", ""
                        )
                        break
                    
                    # فقط وقتی درصد تغییر کرده یا حداقل 2 ثانیه گذشته آپدیت کن
                    if percentage != last_percentage:
                        await download_manager.update_progress_in_bot(
                            update, 
                            context, 
                            message_id, 
                            user_id,
                            percentage,
                            speed,
                            eta
                        )
                        last_percentage = percentage
                    
                    await asyncio.sleep(1)
            
            user_id = update.effective_user.id
            progress_task = asyncio.create_task(update_progress(user_id, progress_message.message_id))
            
            file_path, status = await download_manager.download_and_convert(
                track_url, 
                title, 
                format_choice,
                user_id
            )
            
            await asyncio.sleep(0.5)
            if not progress_task.done():
                progress_task.cancel()
            
            if file_path and os.path.exists(file_path):
                file_size = get_file_size_mb(file_path)
                
                await asyncio.sleep(0.5)
                
                try:
                    with open(file_path, 'rb') as audio_file:
                        audio_data = audio_file.read()
                    
                    audio_stream = BytesIO(audio_data)
                    file_ext = file_path.split('.')[-1]
                    audio_stream.name = f"{title}.{file_ext}"
                    
                    caption = f"🎵 **{title}**\n👨‍🎤 {artist}\n💾 حجم: {file_size} MB\n🎯 فرمت: {format_display}"
                    
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=audio_stream,
                        caption=caption,
                        parse_mode='Markdown',
                        title=title[:64],
                        performer=artist[:64],
                        read_timeout=60,
                        write_timeout=60,
                        connect_timeout=60
                    )
                    
                    # حذف پیام پیشرفت
                    try:
                        await context.bot.delete_message(
                            chat_id=query.message.chat_id,
                            message_id=progress_message.message_id
                        )
                    except:
                        pass
                    
                    success_text = f"""
✅ **دانلود و ارسال موفق!**

🎵 **آهنگ:** {title}
👨‍🎤 **خواننده:** {artist}
💾 **حجم فایل:** {file_size} MB
🎯 **فرمت:** {format_display}

🔍 **برای جستجوی جدید:**
نام آهنگ یا خواننده را بفرستید.
"""
                    if update.effective_user.id == ADMIN_ID:
                        await query.message.reply_text(
                            success_text,
                            parse_mode='Markdown',
                            reply_markup=_admin_reply_keyboard()
                        )
                    else:
                        await query.message.reply_text(
                            success_text,
                            parse_mode='Markdown',
                            reply_markup=_inline_menu_keyboard()
                        )
                    
                    delete_time = time.time() + 30  # بعد از 30 ثانیه حذف شود
                    delete_queue.put((file_path, delete_time))
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"خطا در ارسال فایل: {error_msg}")
                    await query.message.reply_text(f"❌ خطا در ارسال فایل: {error_msg[:100]}")
                
            else:
                await query.message.reply_text(f"❌ خطا در دانلود: {status}")
        
        except Exception as e:
            error_msg = str(e)
            
            if "ffmpeg" in error_msg.lower():
                error_msg = "❌ **خطا:** برای تبدیل فرمت نیاز به FFmpeg است.\n\nلطفاً FFmpeg را نصب کنید یا فرمت دیگری انتخاب کنید."
            elif "timeout" in error_msg.lower():
                error_msg = "❌ **خطا:** زمان انجام عملیات به پایان رسید.\n\nلطفاً دوباره تلاش کنید."
            else:
                error_msg = f"❌ **خطا:** {error_msg[:150]}"
            
            await query.message.reply_text(error_msg, parse_mode='Markdown')
    
    elif data == "back_to_list":
        await show_results_page(update, context)
    
    elif data == "back_to_quality":
        track = context.user_data.get('selected_track')
        if track:
            title = clean_text(track['title'])
            artist = clean_text(track['uploader'])
            duration = format_duration(track['duration'])
            size_mb = track['estimated_size']
            
            info_text = f"""
🎵 **{title}**
👨‍🎤 **خواننده:** {artist}
⏱ **مدت زمان:** {duration}
💾 **حجم تخمینی:** {size_mb} MB

👇 **لطفاً کیفیت مورد نظر را انتخاب کنید:**
"""
            
            keyboard = [
                [InlineKeyboardButton("🎵 کیفیت 128kbps", callback_data="quality_128")],
                [InlineKeyboardButton("🔊 کیفیت 320kbps", callback_data="quality_320")],
                [InlineKeyboardButton("🎧 کیفیت اصلی", callback_data="quality_original")],
                [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="back_to_list")]
            ]
            
            await query.edit_message_text(
                text=info_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    
    elif data == "new_search":
        await query.message.reply_text(
            "🔍 **برای جستجوی آهنگ جدید:**\n`/search [عبارت جستجو]`", 
            parse_mode='Markdown'
        )

async def list_users_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    """نمایش صفحه لیست کاربران"""
    query = update.callback_query
    await query.answer()
    
    users = get_user_list(page=page, per_page=50)
    total_users = get_total_users_count()
    total_pages = (total_users + 49) // 50
    
    if not users:
        await query.edit_message_text("📭 هیچ کاربری یافت نشد.")
        return
    
    list_text = f"📋 لیست کاربران (صفحه {page + 1} از {total_pages})\n\n"
    
    for idx, user in enumerate(users, start=1):
        user_id, username, first_name, last_name, last_seen, usage_count = user
        
        # ساخت نام نمایشی
        display_name = ""
        if first_name:
            display_name += first_name
        if last_name:
            display_name += f" {last_name}"
        if not display_name.strip():
            display_name = "کاربر"
        
        # ساخت نام کاربری
        display_username = f"@{username}" if username else "@-"
        
        # تبدیل تاریخ آخرین فعالیت
        last_seen_jalali = convert_to_jalali(last_seen)
        
        list_text += f"👤 {display_name} | 🆔 {display_username} | 🔁 {usage_count} | 🕒 {last_seen_jalali}\n"
    
    # اضافه کردن دکمه‌های ناوبری
    keyboard = []
    nav_row = []
    
    if page > 0:
        nav_row.append(InlineKeyboardButton("⏪ صفحه قبلی", callback_data=f"users_page_{page-1}"))
    
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("صفحه بعدی ⏩", callback_data=f"users_page_{page+1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("📊 آمار کاربران", callback_data="users_stats")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(list_text, reply_markup=reply_markup)

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کاربران"""
    query = update.callback_query
    await query.answer()
    
    stats = get_user_stats()
    
    stats_text = (
        "📊 آمار کاربران\n"
        "────────────────\n"
        f"👥 کل کاربران: {stats['total']}\n"
        "────────────────\n"
        f"🗓️ امروز: {stats['today']}\n"
        f"⏱️ ۱ ساعت اخیر: {stats['last_1h']}\n"
        f"⏱️ ۳ ساعت اخیر: {stats['last_3h']}\n"
        f"🕘 ۲۴ ساعت اخیر: {stats['last_24h']}\n"
        f"🗓️ ۱ ماه اخیر: {stats['last_30d']}\n"
        f"🗓️ ۳ ماه اخیر: {stats['last_90d']}\n"
        f"🗓️ ۳ سال اخیر: {stats['last_3y']}\n"
    )
    
    keyboard = [[InlineKeyboardButton("📋 لیست کاربران", callback_data="users_page_0")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پیام‌های متنی"""
    if not await ensure_channel_member(update, context):
        return

    user_id = update.effective_user.id
    text = update.message.text
    
    # ???????? ?? ???? ?????? SoundCloud
    if is_soundcloud_url(text):
        await handle_soundcloud_link(update, context, text.strip())
        return
    
    # اگر کاربر ادمین است
    if user_id == ADMIN_ID:
        if text == "📊 آمار کاربران":
            await stats_command(update, context)
        elif text == "📋 لیست کاربران":
            await list_users_command(update, context)
        elif text == "🔍 جستجوی موزیک":
            await update.message.reply_text("🔍 **اسم خواننده یا آهنگ رو بنویسید:**", parse_mode='Markdown')
        elif text == "🎵 دانلود موزیک":
            await update.message.reply_text("🎵 **لینک آهنگ SoundCloud را بفرستید تا دانلود شود.**", parse_mode='Markdown')
        elif text == "ℹ️ راهنمای بات":
            await update.message.reply_text(_help_text(), parse_mode='Markdown')
        else:
            # اگر پیام متنی معمولی است، به عنوان جستجو در نظر بگیر
            if len(text) > 1:
                context.args = text.split()
                await search_command(update, context)
    else:
        # برای کاربران عادی، پیام را به عنوان جستجو در نظر بگیر
        if len(text) > 1:
            context.args = text.split()
            await search_command(update, context)

# --- تابع اصلی ---
def main():
    """تابع اصلی اجرای ربات"""
    print("=" * 60)
    print("🤖 **ربات دانلود موزیک - نسخه نهایی**")
    print("🔗 @PIMX_SONIC_BOT")
    print("⚡ **ویژگی‌های جدید:**")
    print("   • نصب خودکار FFmpeg")
    print("   • نمایش پیشرفت واقعی")
    print("   • حذف خودکار فایل‌ها بعد از ۳۰ ثانیه")
    print("   • سرعت ارسال بهبود یافته")
    print("   • پشتیبانی از فرمت MP4")
    print("   • سیستم آمار و لیست کاربران برای ادمین")
    print("=" * 60)
    
    print("🚀 در حال راه‌اندازی...")
    
    # ایجاد دیتابیس کاربران
    init_database()
    
    # نصب FFmpeg
    if not install_ffmpeg():
        print("⚠️  هشدار: FFmpeg نصب نشد. تبدیل به MP4 ممکن نخواهد بود.")
        print("💡 می‌توانید از فرمت‌های MP3 یا M4A استفاده کنید.")
    
    # بررسی و نصب وابستگی‌ها
    print("\n🔍 بررسی وابستگی‌ها...")
    
    try:
        import yt_dlp
        print("✅ yt-dlp نصب شده است")
    except ImportError:
        print("📦 در حال نصب yt-dlp...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
        print("✅ yt-dlp نصب شد")
    
    try:
        import telegram
        print("✅ python-telegram-bot نصب شده است")
    except ImportError:
        print("📦 در حال نصب python-telegram-bot...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot"])
        print("✅ python-telegram-bot نصب شد")
    
    try:
        import aiohttp
        print("✅ aiohttp نصب شده است")
    except ImportError:
        print("📦 در حال نصب aiohttp...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
        print("✅ aiohttp نصب شد")
    
    try:
        import jdatetime
        print("✅ jdatetime نصب شده است")
    except ImportError:
        print("📦 در حال نصب jdatetime...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "jdatetime"])
        print("✅ jdatetime نصب شد")
    
    # حلقه پایدار برای ری‌استارت در صورت خطا
    backoff = 5
    max_backoff = 60
    while True:
        try:
            # ایجاد یک event loop جدید برای ویندوز
            if platform.system() == "Windows":
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            application = (
                Application.builder()
                .token(TOKEN)
                .read_timeout(60)
                .write_timeout(60)
                .connect_timeout(60)
                .pool_timeout(60)
                .build()
            )
            
            # اضافه کردن هندلرها
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("stats", stats_command))
            application.add_handler(CommandHandler("users", list_users_command))
            application.add_handler(CommandHandler("search", search_command))
            application.add_handler(CallbackQueryHandler(button_handler))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            
            print("=" * 60)
            print("✅ **ربات فعال شد!**")
            print("🤖 نام: PIMXSONIC")
            print("🔗 آدرس: t.me/PIMX_SONIC_BOT")
            print("👑 ادمین: @PIMXPASS")
            print("⏱ حذف فایل‌ها: ۳۰ ثانیه پس از ارسال")
            print("📊 سیستم آمار کاربران فعال")
            print("=" * 60)
            
            # اجرای ربات در event loop فعلی
            application.run_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES,
                close_loop=False
            )

            # اگر run_polling بدون خطا خارج شد، backoff را ریست کن و دوباره بالا بیا.
            backoff = 5
            
        except KeyboardInterrupt:
            print("\n🛑 ربات متوقف شد.")
            break
        except Exception as e:
            print(f"❌ خطا: {e}")
            try:
                import traceback
                traceback.print_exc()
            except:
                pass
            # تاخیر افزایشی برای جلوگیری از کرش پشت سرهم
            print(f"🔁 تلاش مجدد تا {backoff} ثانیه دیگر...")
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)

# --- اجرا ---
if __name__ == '__main__':
    main()
