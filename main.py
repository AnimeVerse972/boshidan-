import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from keep_alive import keep_alive
from database import get_user_by_tg_id, add_user  # ✅ databasedan import

keep_alive()
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    tg_id = str(message.from_user.id)
    user = get_user_by_tg_id(tg_id)
    if not user:
        add_user(tg_id)
    await message.answer("Salom! Bot ishga tushdi 🚀")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("/start - boshlash\n/help - yordam")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
