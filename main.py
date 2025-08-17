import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from keep_alive import keep_alive

# ====== DATABASE IMPORT ======
from database import add_channel, delete_channel, get_channels

# ====== ENV ======
keep_alive()
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")  # ✅ Aiogram 3.7.0 usuli
)
dp = Dispatcher()

# ====== ADMIN PANEL ======
def admin_panel_kb():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📡 Kanallar", callback_data="channels_menu")]
        ]
    )
    return kb


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    await message.answer("🔐 Admin panel", reply_markup=admin_panel_kb())


# ====== KANALLAR MENYUSI ======
def channels_menu_kb():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Asosiy kanallar", callback_data="main_channels")],
            [InlineKeyboardButton(text="✅ Majburiy obuna", callback_data="forced_channels")],
            [InlineKeyboardButton(text="◀️ Ortga", callback_data="back_admin")]
        ]
    )
    return kb


@dp.callback_query(F.data == "channels_menu")
async def channels_menu(call: types.CallbackQuery):
    await call.message.edit_text("📡 Qaysi turdagi kanallarni boshqaramiz?", reply_markup=channels_menu_kb())


# ====== TUR BO'YICHA MENYU (ASOSIY / MAJBURIY) ======
def channel_actions_kb(channel_type: str):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Qo‘shish", callback_data=f"add_{channel_type}")],
            [InlineKeyboardButton(text="➖ O‘chirish", callback_data=f"delete_{channel_type}")],
            [InlineKeyboardButton(text="📋 Ro‘yxat", callback_data=f"list_{channel_type}")],
            [InlineKeyboardButton(text="◀️ Ortga", callback_data="channels_menu")]
        ]
    )
    return kb


@dp.callback_query(F.data.in_(["main_channels", "forced_channels"]))
async def manage_channels(call: types.CallbackQuery):
    channel_type = "main" if call.data == "main_channels" else "forced"
    await call.message.edit_text(
        f"📡 { 'Asosiy' if channel_type=='main' else 'Majburiy obuna' } kanallarni boshqarish",
        reply_markup=channel_actions_kb(channel_type)
    )


# ====== QO‘SHISH ======
@dp.callback_query(F.data.startswith("add_"))
async def add_channel_handler(call: types.CallbackQuery):
    channel_type = call.data.split("_")[1]
    await call.message.answer(
        f"➕ { 'Asosiy' if channel_type=='main' else 'Majburiy obuna' } kanal linkini yuboring:"
    )

    @dp.message(F.text)
    async def get_channel_link(message: types.Message):
        link = message.text.strip()
        add_channel(link, channel_type)
        await message.answer("✅ Kanal qo‘shildi!", reply_markup=channels_menu_kb())


# ====== O‘CHIRISH ======
@dp.callback_query(F.data.startswith("delete_"))
async def delete_channel_handler(call: types.CallbackQuery):
    channel_type = call.data.split("_")[1]
    await call.message.answer(
        f"➖ { 'Asosiy' if channel_type=='main' else 'Majburiy obuna' } kanal linkini yuboring (o‘chirish uchun):"
    )

    @dp.message(F.text)
    async def get_channel_link(message: types.Message):
        link = message.text.strip()
        delete_channel(link, channel_type)
        await message.answer("❌ Kanal o‘chirildi!", reply_markup=channels_menu_kb())


# ====== RO‘YXAT ======
@dp.callback_query(F.data.startswith("list_"))
async def list_channels_handler(call: types.CallbackQuery):
    channel_type = call.data.split("_")[1]
    channels = get_channels(channel_type)

    if not channels:
        text = "📭 Hech qanday kanal yo‘q."
    else:
        text = "📋 Ro‘yxat:\n\n" + "\n".join([f"• {c.link}" for c in channels])

    await call.message.edit_text(text, reply_markup=channel_actions_kb(channel_type))


# ====== ORTGA ======
@dp.callback_query(F.data == "back_admin")
async def back_admin(call: types.CallbackQuery):
    await call.message.edit_text("🔐 Admin panel", reply_markup=admin_panel_kb())


# ====== START ======
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Salom! Bot ishga tushdi 🚀")


# ====== MAIN ======
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
