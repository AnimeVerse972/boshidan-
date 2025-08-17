import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from dotenv import load_dotenv
from keep_alive import keep_alive
from database import (
    get_user_by_tg_id, add_user,
    get_required_channels, get_main_channels
)

# === Boshlang'ich sozlash ===
keep_alive()
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()


# === Foydalanuvchini obuna bo‘lganini tekshirish ===
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


# === Asosiy komandalar ===
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
    await message.answer("/start - boshlash\n/help - yordam\n/admin - admin panel (faqat admin)")


# === Admin panel ===
admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📢 Kanallar")],
    ],
    resize_keyboard=True
)


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return await message.answer("❌ Siz admin emassiz!")
    await message.answer("🔐 Admin panel:", reply_markup=admin_kb)


# === Kanallar menyusi ===
@dp.message(lambda m: m.text == "📢 Kanallar")
async def show_channel_types(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Asosiy kanallar", callback_data="show_main_channels")],
            [InlineKeyboardButton(text="🔒 Majburiy obuna kanallari", callback_data="show_required_channels")]
        ]
    )
    await message.answer("Qaysi turdagi kanallarni ko‘rmoqchisiz?", reply_markup=kb)


# === Inline tugmalar: Qo‘shish / O‘chirish / Ro‘yxat ===
def channel_actions_kb(channel_type: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Qo‘shish", callback_data=f"{channel_type}_add")],
            [InlineKeyboardButton(text="❌ O‘chirish", callback_data=f"{channel_type}_delete")],
            [InlineKeyboardButton(text="📃 Ro‘yxat", callback_data=f"{channel_type}_list")],
        ]
    )


@dp.callback_query(lambda c: c.data in ["show_main_channels", "show_required_channels"])
async def process_channel_type(callback: types.CallbackQuery):
    if str(callback.from_user.id) != str(ADMIN_ID):
        return await callback.answer("Siz admin emassiz!", show_alert=True)

    if callback.data == "show_main_channels":
        await bot.send_sticker(
            chat_id=callback.message.chat.id,
            sticker="CAACAgIAAxkBAAEIu4Bn7l1Uu1zyH6R0Lmi5y0R2R7r0YAACsQADVp29CjepXdmDpdXzNAQ"
        )
        await callback.message.answer(
            "📢 <b>Asosiy kanallar</b> bo‘limi.\n"
            "➕ Qo‘shish — yangi asosiy kanal qo‘shasiz\n"
            "❌ O‘chirish — mavjud kanalni o‘chirasiz\n"
            "📃 Ro‘yxat — barcha asosiy kanallarni ko‘rasiz",
            reply_markup=channel_actions_kb("main")
        )

    elif callback.data == "show_required_channels":
        await bot.send_sticker(
            chat_id=callback.message.chat.id,
            sticker="CAACAgIAAxkBAAEIu4Jn7l2EQE2ZP8Nq-3-2TkcdqZo6awACsAADVp29CmKInA7P9RvRNAQ"
        )
        await callback.message.answer(
            "🔒 <b>Majburiy obuna kanallari</b> bo‘limi.\n"
            "➕ Qo‘shish — yangi majburiy kanal qo‘shasiz\n"
            "❌ O‘chirish — mavjud majburiy kanalni o‘chirasiz\n"
            "📃 Ro‘yxat — barcha majburiy kanallarni ko‘rasiz",
            reply_markup=channel_actions_kb("required")
        )

    await callback.answer()


# === Tugma bosilganda ishlaydiganlar ===
@dp.callback_query(lambda c: c.data.endswith("_add"))
async def add_channel_handler(callback: types.CallbackQuery):
    await callback.answer("➕ Kanal qo‘shish funksiyasi hali yozilmagan", show_alert=True)


@dp.callback_query(lambda c: c.data.endswith("_delete"))
async def delete_channel_handler(callback: types.CallbackQuery):
    await callback.answer("❌ Kanal o‘chirish funksiyasi hali yozilmagan", show_alert=True)


@dp.callback_query(lambda c: c.data.endswith("_list"))
async def list_channel_handler(callback: types.CallbackQuery):
    if callback.data.startswith("main"):
        channels = get_main_channels()
        text = "📢 Asosiy kanallar ro‘yxati:\n"
        if channels:
            for ch in channels:
                text += f"• {ch.channel_id} ({ch.invite_link or 'link yo‘q'})\n"
        else:
            text += "🚫 Hali qo‘shilmagan"
    else:
        channels = get_required_channels()
        text = "🔒 Majburiy obuna kanallari ro‘yxati:\n"
        if channels:
            for ch in channels:
                text += f"• {ch.channel_id} ({ch.invite_link or 'link yo‘q'})\n"
        else:
            text += "🚫 Hali qo‘shilmagan"

    await callback.message.answer(text)
    await callback.answer()


# === Run bot ===
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
