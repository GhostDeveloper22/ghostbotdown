import os
import asyncio
import yt_dlp
import sqlite3
import time

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 977114742

bot = Bot(token=TOKEN)
dp = Dispatcher()

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

# антиспам
user_last_request = {}

def check_rate_limit(user_id):
    now = time.time()

    if user_id in user_last_request:
        if now - user_last_request[user_id] < 5:
            return False

    user_last_request[user_id] = now
    return True


def download_media(url):

    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(id)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,

        'cookiefile': 'cookies.txt',

        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
            'Accept-Language': 'en-US,en;q=0.9'
        },

        'retries': 5,
        'sleep_interval': 2
    }

    files = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if 'entries' in info:
            for entry in info['entries']:
                filename = ydl.prepare_filename(entry)
                files.append(filename)
        else:
            filename = ydl.prepare_filename(info)
            files.append(filename)

    return files


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

    await message.answer(f"📊 Пользователей: {users}")


@dp.message()
async def download(message: Message):

    user_id = message.from_user.id

    if not check_rate_limit(user_id):
        await message.answer("⏳ Подожди несколько секунд")
        return

    if not message.text:
        return

    url = message.text.strip()

    if len(url) > 300:
        await message.answer("❌ Слишком длинная ссылка")
        return

    if not url.startswith("http"):
        await message.answer("Отправь ссылку")
        return

    if not any(site in url for site in [
        "tiktok.com",
        "instagram.com",
        "youtube.com",
        "youtu.be"
    ]):
        await message.answer("❌ Поддерживаются только TikTok, Instagram и YouTube")
        return

    msg = await message.answer("⬇️ Скачиваю...")

    try:

        files = download_media(url)

        for file in files:

            if not os.path.exists(file):
                continue

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

            os.remove(file)

        await msg.delete()

    except Exception as e:
        print(e)
        await message.answer(f"Ошибка: {e}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())