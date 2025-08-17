import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from keep_alive import keep_alive
from database import add_user, get_channels, add_channel, delete_channel

load_dotenv()
keep_alive()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN, default=types.DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# === Majburiy obuna tekshirish ===
async def check_forced_subscription(user_id: int) -> bool:
    forced_channels = get_channels("forced")

    for ch in forced_channels:
        try:
            member = await bot.get_chat_member(chat_id=ch.link, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except TelegramForbiddenError:
            return False
        except Exception:
            return False
    return True


# === ADMIN PANEL TUGMALARI ===
def admin_panel():
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Kanallar", callback_data="channels")
    return kb.as_markup()


def channel_types_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔹 Asosiy kanallar", callback_data="channel_main")
    kb.button(text="🔒 Majburiy obuna", callback_data="channel_forced")
    kb.button(text="⬅️ Ortga", callback_data="back_admin")
    kb.adjust(1)
    return kb.as_markup()


def channel_manage_kb(channel_type: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Qo‘shish", callback_data=f"add_{channel_type}")
    kb.button(text="➖ O‘chirish", callback_data=f"delete_{channel_type}")
    kb.button(text="📜 Ro‘yxat", callback_data=f"list_{channel_type}")
    kb.button(text="⬅️ Ortga", callback_data="channels")
    kb.adjust(1)
    return kb.as_markup()


# === KOMANDALAR ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    tg_id = str(message.from_user.id)
    add_user(tg_id)

    # majburiy obuna tekshir
    subscribed = await check_forced_subscription(message.from_user.id)
    if not subscribed:
        forced_channels = get_channels("forced")
        text = "❗ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:\n\n"
        for ch in forced_channels:
            text += f"👉 {ch.link}\n"
        text += "\n✅ Obuna bo‘lgach, /start ni qaytadan bosing."
        await message.answer(text)
        return

    await message.answer("Salom! Bot ishga tushdi 🚀")


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    await message.answer("🔧 Admin panel", reply_markup=admin_panel())


# === CALLBACKLAR ===
@dp.callback_query(F.data == "channels")
async def cb_channels(callback: types.CallbackQuery):
    await callback.message.edit_text("🔹 Qaysi turdagi kanallarni tanlaysiz?", reply_markup=channel_types_kb())


@dp.callback_query(F.data == "back_admin")
async def cb_back_admin(callback: types.CallbackQuery):
    await callback.message.edit_text("🔧 Admin panel", reply_markup=admin_panel())


@dp.callback_query(F.data.startswith("channel_"))
async def cb_channel_type(callback: types.CallbackQuery):
    channel_type = callback.data.split("_")[1]
    await callback.message.edit_text(
        f"📢 Tanlangan tur: <b>{'Asosiy' if channel_type=='main' else 'Majburiy obuna'}</b>",
        reply_markup=channel_manage_kb(channel_type)
    )


# === Qo‘shish, o‘chirish, ro‘yxat ===
@dp.callback_query(F.data.startswith("add_"))
async def cb_add_channel(callback: types.CallbackQuery, state: types.FSMContext):
    channel_type = callback.data.split("_")[1]
    await callback.message.answer("➕ Kanal linkini yuboring:")
    await state.update_data(channel_type=channel_type, action="add")


@dp.callback_query(F.data.startswith("delete_"))
async def cb_delete_channel(callback: types.CallbackQuery, state: types.FSMContext):
    channel_type = callback.data.split("_")[1]
    await callback.message.answer("❌ O‘chirish uchun kanal linkini yuboring:")
    await state.update_data(channel_type=channel_type, action="delete")


@dp.callback_query(F.data.startswith("list_"))
async def cb_list_channels(callback: types.CallbackQuery):
    channel_type = callback.data.split("_")[1]
    chans = get_channels(channel_type)
    if not chans:
        await callback.message.answer("📭 Hozircha kanallar yo‘q")
    else:
        text = "📜 Ro‘yxat:\n\n" + "\n".join([f"{i+1}. {c.link}" for i, c in enumerate(chans)])
        await callback.message.answer(text)


# === Foydalanuvchi kanal link yuborganda ===
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

dp = Dispatcher(storage=MemoryStorage())


@dp.message(F.text.startswith("http"))
async def process_channel_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if not data:
        return

    channel_type = data.get("channel_type")
    action = data.get("action")
    link = message.text.strip()

    if action == "add":
        add_channel(link, channel_type)
        await message.answer("✅ Kanal qo‘shildi", reply_markup=channel_manage_kb(channel_type))
    elif action == "delete":
        delete_channel(link, channel_type)
        await message.answer("❌ Kanal o‘chirildi", reply_markup=channel_manage_kb(channel_type))

    await state.clear()


# === START POLLING ===
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
