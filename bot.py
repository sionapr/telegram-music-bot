import telebot
from telebot import types
from ShazamAPI import Shazam
from pydub import AudioSegment, effects
import yt_dlp
import os
import hashlib
import threading

# =========================================
# CONFIG
# =========================================

TOKEN = "8788976547:AAEVQZOqWCN4QfIDTxjzf1XMsoohcUT71WM"

bot = telebot.TeleBot(TOKEN)

DOWNLOAD_PATH = "downloads"

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

# =========================================
# TELEGRAM COMMANDS
# =========================================

bot.set_my_commands([
    telebot.types.BotCommand("start", "شروع ربات")
])

# =========================================
# USER MODE
# =========================================

user_mode = {}

# =========================================
# CACHE
# =========================================

music_cache = {}

# =========================================
# MENUS
# =========================================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🎵 جستجوی آهنگ با ویدیو")
    btn2 = types.KeyboardButton("📥 دانلود ریلز / ویدیو اینستاگرام")
    btn3 = types.KeyboardButton("ℹ️ راهنما")
    markup.add(btn1, btn2, btn3)
    return markup

def back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("🔙 بازگشت")
    markup.add(btn)
    return markup

# =========================================
# START
# =========================================

@bot.message_handler(commands=['start'])
def start(message):
    user_mode[message.chat.id] = "menu"
    bot.send_message(
        message.chat.id,
        "🔥 ربات حرفه‌ای تشخیص آهنگ روشن است\n\nاز منو گزینه موردنظر را انتخاب کن",
        reply_markup=main_menu()
    )

# =========================================
# HELP
# =========================================

@bot.message_handler(func=lambda m: m.text == "ℹ️ راهنما")
def help_menu(message):
    bot.send_message(
        message.chat.id,
        "🎵 امکانات ربات:\n\n"
        "• تشخیص حرفه‌ای آهنگ\n"
        "• تشخیص از ویس و ویدیو\n"
        "• دانلود نسخه کامل آهنگ\n"
        "• دانلود ریلز اینستاگرام\n"
        "• دقت بسیار بالا"
    )

# =========================================
# MUSIC MENU
# =========================================

@bot.message_handler(func=lambda m: m.text == "🎵 جستجوی آهنگ با ویدیو")
def music_menu(message):
    user_mode[message.chat.id] = "music"
    bot.send_message(message.chat.id, "📥 حالا ویس، آهنگ یا ویدیو بفرست", reply_markup=back_menu())

# =========================================
# INSTAGRAM MENU
# =========================================

@bot.message_handler(func=lambda m: m.text == "📥 دانلود ریلز / ویدیو اینستاگرام")
def instagram_menu(message):
    user_mode[message.chat.id] = "instagram"
    bot.send_message(message.chat.id, "🔗 لینک ریلز یا ویدیوی اینستاگرام را بفرست", reply_markup=back_menu())

# =========================================
# BACK
# =========================================

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت")
def back(message):
    user_mode[message.chat.id] = "menu"
    bot.send_message(message.chat.id, "🏠 برگشتی به منوی اصلی", reply_markup=main_menu())

# =========================================
# HASH
# =========================================

def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

# =========================================
# CLEAN AUDIO
# =========================================

def clean_audio(input_file, output_file):
    audio = AudioSegment.from_file(input_file)
    audio = effects.normalize(audio)
    audio = audio.low_pass_filter(10000)
    audio = audio.high_pass_filter(150)
    audio = audio.set_channels(2)
    audio = audio.set_frame_rate(44100)
    audio.export(output_file, format="mp3", bitrate="320k")

# =========================================
# DOWNLOAD SONG
# =========================================

def download_mp3(query):
    output_file = f"{DOWNLOAD_PATH}/song.%(ext)s"

    for file in os.listdir(DOWNLOAD_PATH):
        if file.startswith("song."):
            try:
                os.remove(os.path.join(DOWNLOAD_PATH, file))
            except:
                pass

    try:
        print("[CMD] SoundCloud Search")
        ydl_search = {'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_search) as ydl:
            info = ydl.extract_info(f"scsearch10:{query}", download=False)
            if info and "entries" in info:
                for entry in info["entries"]:
                    if not entry:
                        continue
                    title = str(entry.get("title", "")).lower()
                    if query.split()[0].lower() in title:
                        link = entry["webpage_url"]
                        print("[SC FOUND]", link)
                        ydl_opts = {
                            'format': 'bestaudio',
                            'outtmpl': output_file,
                            'noplaylist': True,
                            'quiet': False,
                            'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '320',
                            }],
                        }
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                            ydl2.download([link])
                        return f"{DOWNLOAD_PATH}/song.mp3"
    except Exception as e:
        print("[SC ERROR]", e)

    try:
        print("[CMD] YouTube Fallback")
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': output_file,
            'noplaylist': True,
            'quiet': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0'
            },
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])
        print("[YT DOWNLOADED]")
        return f"{DOWNLOAD_PATH}/song.mp3"
    except Exception as e:
        print("[YT ERROR]", e)
    return None

# =========================================
# DOWNLOAD INSTAGRAM VIDEO
# =========================================

def download_instagram_video(url):
    try:
        print("[CMD] Instagram Download")
        for file in os.listdir():
            if file.startswith("instagram_video"):
                try: os.remove(file)
                except: pass
        ydl_opts = {
            'outtmpl': 'instagram_video.%(ext)s',
            'format': 'best',
            'merge_output_format': 'mp4',
            'quiet': False,
            'noplaylist': True,
            'cookiefile': 'instagram_cookies.txt',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://www.instagram.com/',
            },
            'nocheckcertificate': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for file in os.listdir():
            if file.startswith("instagram_video"):
                print("[IG SUCCESS]")
                return file
    except Exception as e:
        print("[IG ERROR]", e)
    return None

# =========================================
# INSTAGRAM HANDLER
# =========================================

@bot.message_handler(func=lambda m: user_mode.get(m.chat.id) == "instagram")
def instagram_download(message):
    try:
        url = message.text
        if "instagram.com" not in url:
            bot.reply_to(message, "❌ لینک اینستاگرام نیست")
            return
        bot.reply_to(message, "⬇️ درحال دانلود ویدیو...")
        video_path = download_instagram_video(url)
        if not video_path:
            bot.reply_to(message, "❌ دانلود ناموفق بود")
            return
        with open(video_path, "rb") as video:
            bot.send_video(message.chat.id, video)
        os.remove(video_path)
        bot.send_message(message.chat.id, "✅ ویدیو ارسال شد")
    except Exception as e:
        print("[IG ERROR]", e)
        bot.reply_to(message, "❌ خطا در دانلود")

# =========================================
# MUSIC HANDLER
# =========================================

@bot.message_handler(content_types=['voice', 'audio', 'video'])
def recognize_music(message):
    if user_mode.get(message.chat.id) != "music":
        bot.reply_to(message, "❌ اول گزینه «جستجوی آهنگ با ویدیو» را بزن")
        return
    threading.Thread(target=process_music, args=(message,)).start()

# =========================================
# PROCESS MUSIC
# =========================================

def process_music(message):
    try:
        bot.reply_to(message, "🔍 درحال پردازش حرفه‌ای...")
        if message.content_type == 'voice':
            file_id = message.voice.file_id
        elif message.content_type == 'audio':
            file_id = message.audio.file_id
        else:
            file_id = message.video.file_id
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        if message.content_type == 'video':
            with open("video.mp4", "wb") as f: f.write(downloaded)
            os.system('ffmpeg -y -i video.mp4 -vn -acodec mp3 raw_music.mp3')
        else:
            with open("voice.ogg", "wb") as f: f.write(downloaded)
            audio = AudioSegment.from_file("voice.ogg")
            audio.export("raw_music.mp3", format="mp3")
        clean_audio("raw_music.mp3", "music.mp3")
        music_md5 = file_hash("music.mp3")
        if music_md5 in music_cache:
            cached_file = music_cache[music_md5]
            with open(cached_file, "rb") as audio: bot.send_audio(message.chat.id, audio)
            return
        with open("music.mp3", "rb") as f:
            shazam = Shazam(f.read())
            result = next(shazam.recognizeSong())
        if not result[1] or "track" not in result[1]:
            bot.reply_to(message, "❌ آهنگ پیدا نشد")
            return
        song = result[1]["track"]["title"]
        artist = result[1]["track"]["subtitle"]
        query = f"{song} {artist}"
        cover = result[1]["track"]["images"]["coverart"]
        caption = f"🎵 {song}\n👤 {artist}\n\n⬇️ دانلود نسخه کامل..."
        bot.send_photo(message.chat.id, cover, caption=caption)
        mp3_path = download_mp3(query)
        if not mp3_path: bot.reply_to(message, "❌ دانلود ناموفق بود"); return
        with open(mp3_path, "rb") as audio:
            bot.send_audio(message.chat.id, audio, title=song, performer=artist)
        music_cache[music_md5] = mp3_path
        for file in ["music.mp3", "raw_music.mp3", "voice.ogg", "video.mp4"]:
            if os.path.exists(file): os.remove(file)
    except Exception as e:
        print("[ERROR]", e)
        bot.reply_to(message, "❌ خطا در پردازش")

# =========================================
# RUN
# =========================================

print("🤖 Professional Music Bot Running...")
print("⚠️ instagram_cookies.txt کنار bot.py باشد")

bot.infinity_polling(timeout=60, long_polling_timeout=60)
