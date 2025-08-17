import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from keep_alive import keep_alive
from database import (
    get_user_by_tg_id, add_user,
    add_required_channel, get_required_channels,
    add_main_channel, get_main_channels
)

keep_alive()
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()


# ✅ Foydalanuvchi obunasini tekshirish
async def check_subscriptions(user_id: int):
    channels = get_required_channels()
    not_subscribed = []

    for ch in channels:
        try:
            member = await bot.get_chat_member(ch.channel_id, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_subscribed.append(ch)
        except Exception:
            not_subscribed.append(ch)  # private yoki xatolik bo‘lsa ham

    return not_subscribed


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    tg_id = str(message.from_user.id)

    user = get_user_by_tg_id(tg_id)
    if not user:
        add_user(tg_id)

    not_subscribed = await check_subscriptions(message.from_user.id)

    if not_subscribed:
        kb = InlineKeyboardMarkup()
        for ch in not_subscribed:
            if ch.invite_link:
                kb.add(InlineKeyboardButton(text=f"🔗 Kanalga qo‘shilish", url=ch.invite_link))
        await message.answer("❌ Avval quyidagi kanallarga obuna bo‘ling:", reply_markup=kb)
    else:
        await message.answer("✅ Botdan foydalanishingiz mumkin 🚀")


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("/start - boshlash\n/help - yordam")


# ✅ Admin komandasi: asosiy kanallarga xabar yuborish
@dp.message(Command("send_all"))
async def cmd_send_all(message: types.Message):
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):  # faqat admin ishlatsin
        return await message.answer("❌ Siz admin emassiz!")

    text = message.text.replace("/send_all", "").strip()
    if not text:
        return await message.answer("Matn yuboring: /send_all Salom!")

    channels = get_main_channels()
    for ch in channels:
        try:
            await bot.send_message(ch.channel_id, text)
        except Exception as e:
            await message.answer(f"Xato: {e}")

    await message.answer("✅ Xabar barcha asosiy kanallarga yuborildi!")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
