import os
import asyncio
import yt_dlp
import sqlite3
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

ADMIN_ID = 977114742

TOKEN = "8382758539:AAFYl3a2yqxWOlECNiokjtUliofqkvPuxaQ"

bot = Bot(token=TOKEN)
dp = Dispatcher()


def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.%(ext)s',
        'noplaylist': True,
        'http_headers': {
        'User-Agent': 'Mozilla/5.0'
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
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

    url = message.text

    if not url.startswith("http"):
        await message.answer("Отправь ссылку")
        return

    msg = await message.answer("Скачиваю...")

    try:
        file = download_video(url)

        video = FSInputFile(file)

        await message.answer_video(
            video,
            caption="Это видео скачано с помощью @savermetiktok_bot 🤖"
        )

        os.remove(file)

    except Exception as e:
        print(e)
        await message.answer(f"Ошибка: {e}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())