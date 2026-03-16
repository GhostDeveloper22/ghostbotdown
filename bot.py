import os
import asyncio
import yt_dlp
import sqlite3
import time

user_last_request = {}
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import FSInputFile

# база данных
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER UNIQUE
)
""")

conn.commit()

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

user_last_request = {}

def check_rate_limit(user_id):
    now = time.time()

    if user_id in user_last_request:
        if now - user_last_request[user_id] < 5:
            return False

    user_last_request[user_id] = now
    return True

ADMIN_ID = 977114742

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


def download_video(url):
    ydl_opts = {
    'format': 'best',
    'outtmpl': '%(id)s.%(ext)s',
    'quiet': True,
    'noplaylist': True,

    'cookiefile': 'cookies.txt',

    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    },

    'sleep_interval': 2,
    'max_sleep_interval': 5,

    'retries': 5,
    'fragment_retries': 5,

    'extractor_args': {
        'instagram': {
            'api_version': 'v1'
        }
    }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if 'entries' in info:
            info = info['entries'][0]

        filename = ydl.prepare_filename(info)

    return filename


@dp.message(Command("start"))
async def start(message: Message):

    add_user(message.from_user.id)

    await message.answer("Отправь ссылку на видео")

@dp.message(Command("admin"))
async def admin_panel(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    text = f"""
📊 Статистика бота

👤 Пользователей: {users}
"""

    await message.answer(text)

@dp.message()
async def download(message: Message):
       user_id = message.from_user.id

       # анти-спам защита
       if not check_rate_limit(user_id):
           await message.answer("⏳ Подожди несколько секунд перед следующим запросом")
           return
       # защита от длинных сообщений
       if len(message.text) > 300:
           await message.answer("❌ Слишком длинное сообщение")
           return

       url = message.text

       if not url.startswith("http"):
        await message.answer("Отправь ссылку")
        return

       msg = await message.answer("Скачиваю...")
       # проверка разрешённых сайтов
       if not any(site in url for site in [
          "tiktok.com",
          "instagram.com",
          "youtube.com"
        ]):
        await message.answer("❌ Поддерживаются только TikTok, Instagram и YouTube")
        return
       
       try:
            ydl_opts = {
               'format': 'bestvideo+bestaudio/best',
               'merge_output_format': 'mp4',
               'outtmpl': 'video.%(ext)s',
               'noplaylist': True,
               'quiet': True,
               'http_headers': {
               'User-Agent': 'Mozilla/5.0'
            }
        }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
             info = ydl.extract_info(url, download=True)

             files = []

            if 'entries' in info:
              for entry in info['entries']:
               if entry.get("url"):
                 filename = ydl.prepare_filename(entry)
                 files.append(filename)
            
            else:
            
               filename = ydl.prepare_filename(info)
               files.append(filename)

            for file in files:

                file_input = FSInputFile(file)

            if file.endswith(".mp4"):
             await message.answer_video(
                   file_input,
                 caption="Это видео скачано с помощью @savermetiktok_bot 🤖"
        )
            else:
             await message.answer_photo(
                   file_input,
                   caption="Это фото скачано с помощью @savermetiktok_bot 🤖"
        )

            if os.path.exists(file):
              os.remove(file)
        # удаляем видео после отправки
            if os.path.exists(file):
              os.remove(file)

       except Exception as e:
        print(e)
        await message.answer(f"Ошибка: {e}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())