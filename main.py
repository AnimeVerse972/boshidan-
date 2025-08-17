import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties   # <-- MUHIM!
from database import add_channel, delete_channel, get_channels

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# 🔹 ADMIN PANEL
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanallar", callback_data="channels_menu")]
    ])
    await message.answer("🔧 Admin panel:", reply_markup=kb)


# 🔹 Kanal menyusi
@dp.callback_query(F.data == "channels_menu")
async def channels_menu(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Asosiy kanallar", callback_data="main_channels")],
        [InlineKeyboardButton(text="Majburiy obuna kanallari", callback_data="mandatory_channels")],
        [InlineKeyboardButton(text="◀️ Ortga", callback_data="back_admin")]
    ])
    await call.message.edit_text("Qaysi turdagi kanalni tanlaysiz?", reply_markup=kb)


# 🔹 Ortga tugma
@dp.callback_query(F.data == "back_admin")
async def back_admin(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanallar", callback_data="channels_menu")]
    ])
    await call.message.edit_text("🔧 Admin panel:", reply_markup=kb)


# 🔹 Kanal turini tanlash
@dp.callback_query(F.data.in_(["main_channels", "mandatory_channels"]))
async def channel_actions(call: CallbackQuery):
    channel_type = "main" if call.data == "main_channels" else "mandatory"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Qo‘shish", callback_data=f"add_{channel_type}")],
        [InlineKeyboardButton(text="❌ O‘chirish", callback_data=f"del_{channel_type}")],
        [InlineKeyboardButton(text="📋 Ro‘yxat", callback_data=f"list_{channel_type}")],
        [InlineKeyboardButton(text="◀️ Ortga", callback_data="channels_menu")]
    ])
    await call.message.edit_text(
        f"🔧 {channel_type.capitalize()} kanallar boshqaruvi:", reply_markup=kb
    )


# 🔹 Kanal qo‘shish
@dp.callback_query(F.data.startswith("add_"))
async def add_channel_start(call: CallbackQuery, state=None):
    channel_type = call.data.split("_")[1]
    await call.message.answer(
        f"📩 {channel_type.capitalize()} kanal qo‘shish uchun:\n"
        f"1. Kanal ID (masalan: <code>-1001234567890</code>) yuboring\n"
        f"2. Invite link (agar mavjud bo‘lsa)"
    )
    # Bu yerda FSM yozish kerak (agar kerak bo‘lsa), hozir qisqartirilgan


# 🔹 Kanal ro‘yxati
@dp.callback_query(F.data.startswith("list_"))
async def list_channels(call: CallbackQuery):
    channel_type = call.data.split("_")[1]
    channels = get_channels(channel_type)
    if not channels:
        await call.message.edit_text("⚠️ Kanallar yo‘q")
        return

    text = f"📋 {channel_type.capitalize()} kanallar ro‘yxati:\n\n"
    for ch in channels:
        text += f"• ID: <code>{ch.channel_id}</code>\n"
        if ch.invite_link:
            text += f"🔗 {ch.invite_link}\n"
        text += f"(db_id={ch.id})\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Ortga", callback_data=f"{channel_type}_channels")]
    ])
    await call.message.edit_text(text, reply_markup=kb)


# 🔹 Majburiy obuna tekshirish
async def check_subscriptions(user_id: int):
    mandatory_channels = get_channels("mandatory")
    not_joined = []

    for ch in mandatory_channels:
        try:
            member = await bot.get_chat_member(ch.channel_id, user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)

    return not_joined


@dp.message(Command("start"))
async def cmd_start(message: Message):
    not_joined = await check_subscriptions(message.from_user.id)

    if not_joined:
        kb = InlineKeyboardMarkup()
        for ch in not_joined:
            url = ch.invite_link if ch.invite_link else f"https://t.me/{ch.channel_id}"
            kb.add(InlineKeyboardButton(text="🔗 Kanalga qo‘shilish", url=url))
        kb.add(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs"))
        await message.answer("Botdan foydalanish uchun quyidagi kanallarga qo‘shiling:", reply_markup=kb)
        return

    await message.answer("✨")


@dp.callback_query(F.data == "check_subs")
async def recheck(call: CallbackQuery):
    not_joined = await check_subscriptions(call.from_user.id)
    if not_joined:
        await call.answer("⚠️ Hali ham obuna bo‘lmadingiz", show_alert=True)
    else:
        await call.message.edit_text("✅ Obuna tekshirildi! Botdan foydalanishingiz mumkin.")


# 🔹 Run bot
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
