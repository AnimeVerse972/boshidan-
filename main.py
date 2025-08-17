import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from database import init_db, add_channel, delete_channel, get_channels

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin ID
ADMINS = [6486825926]   # <-- bu yerga o'zingizning Telegram ID ni yozasiz

bot = Bot(token=BOT_TOKEN, default=types.bot.DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# === ADMIN TEKSHIRUV DECORATOR ===
def admin_only(handler):
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id not in ADMINS:
            return
        return await handler(message, *args, **kwargs)
    return wrapper


# === OBUNA TEKSHIRISH FUNKSIYASI ===
async def check_subscription(user_id: int) -> bool:
    channels = await get_channels("mandatory")
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch.channel_id, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except TelegramBadRequest:
            return False
    return True


# === START ===
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id

    if user_id in ADMINS:
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📡 Kanallar")]
            ],
            resize_keyboard=True
        )
        await message.answer("🔐 Admin panel:", reply_markup=kb)
    else:
        # obuna tekshir
        if not await check_subscription(user_id):
            channels = await get_channels("mandatory")
            text = "❗️ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:\n\n"
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Kanalga obuna bo‘lish", url=ch.invite_link)]
                    for ch in channels
                ] + [[InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs")]]
            )
            for ch in channels:
                text += f"👉 <a href='{ch.invite_link}'>Kanal</a>\n"
            await message.answer(text, reply_markup=kb)
            return

        # agar obuna bo‘lsa ✨ yuboriladi
        await message.answer_sticker("CAACAgUAAxkBAAIBQmSghd0Kk5Ujv3sKkdJkF0n31_Y9AAKkAgACVp29CnxzjW9-1nS6LwQ")  # ✨ stiker ID
        await message.answer("Xush kelibsiz ✨")


# === SUBS TEKSHIRISH CALLBACK ===
@dp.callback_query(lambda c: c.data == "check_subs")
async def recheck_subs(call: CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.edit_text("✅ Siz barcha kanallarga obuna bo‘ldingiz!")
        await call.message.answer_sticker("CAACAgUAAxkBAAIBQmSghd0Kk5Ujv3sKkdJkF0n31_Y9AAKkAgACVp29CnxzjW9-1nS6LwQ")
    else:
        await call.answer("❌ Hali ham obuna bo‘lmadingiz", show_alert=True)
# === ADMIN PANEL (/admin ham ishlaydi) ===
@dp.message(Command("admin"))
@admin_only
async def admin_cmd(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📡 Kanallar")]],
        resize_keyboard=True
    )
    await message.answer("🔐 Admin panel:", reply_markup=kb)


# === KANALLAR MENYU (INLINE) ===
@dp.message(F.text == "📡 Kanallar")
@admin_only
async def channels_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Asosiy kanallar", callback_data="main_channels")],
        [InlineKeyboardButton(text="✅ Majburiy obuna kanallari", callback_data="mandatory_channels")]
    ])
    await message.answer("Qaysi turdagi kanallarni boshqaramiz?", reply_markup=kb)


# === ASOSIY KANALLAR MENYU ===
@dp.callback_query(F.data == "main_channels")
async def main_channels(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Qo‘shish", callback_data="add_main")],
        [InlineKeyboardButton(text="❌ O‘chirish", callback_data="del_main")],
        [InlineKeyboardButton(text="📋 Ro‘yxat", callback_data="list_main")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="channels_menu")]
    ])
    await call.message.edit_text("📢 Asosiy kanallar menyusi", reply_markup=kb)


# === MAJBURIY KANALLAR MENYU ===
@dp.callback_query(F.data == "mandatory_channels")
async def mandatory_channels(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Qo‘shish", callback_data="add_mandatory")],
        [InlineKeyboardButton(text="❌ O‘chirish", callback_data="del_mandatory")],
        [InlineKeyboardButton(text="📋 Ro‘yxat", callback_data="list_mandatory")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="channels_menu")]
    ])
    await call.message.edit_text("✅ Majburiy obuna kanallar menyusi", reply_markup=kb)


# === KANAL QO‘SHISH ===
@dp.callback_query(F.data.startswith("add_"))
async def add_channel_handler(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    channel_type = call.data.replace("add_", "")
    await call.message.answer(
        "🔗 Kanal <b>ID</b> va <b>invite link</b> yuboring:\n"
        "masalan: <code>-1001234567890 https://t.me/xxxxx</code>"
    )
    dp.workflow_data[call.from_user.id] = channel_type


@dp.message()
async def process_channel_data(message: Message):
    if message.from_user.id not in ADMINS:
        return
    if message.from_user.id not in dp.workflow_data:
        return

    channel_type = dp.workflow_data.pop(message.from_user.id)
    try:
        channel_id, invite_link = message.text.split(" ", 1)
        await add_channel(channel_type, int(channel_id), invite_link)
        await message.answer("✅ Kanal muvaffaqiyatli qo‘shildi!")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")


# === KANALNI O‘CHIRISH ===
@dp.callback_query(F.data.startswith("del_"))
async def delete_channel_handler(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    channel_type = call.data.replace("del_", "")
    channels = await get_channels(channel_type)

    if not channels:
        await call.message.answer("❌ Hech qanday kanal topilmadi.")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{ch.channel_id}", callback_data=f"remove_{ch.channel_id}")]
            for ch in channels
        ] + [[InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"{channel_type}_channels")]]
    )
    await call.message.edit_text("O‘chirish uchun kanalni tanlang:", reply_markup=kb)


@dp.callback_query(F.data.startswith("remove_"))
async def remove_channel(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    channel_id = int(call.data.replace("remove_", ""))
    await delete_channel(channel_id)
    await call.message.edit_text("✅ Kanal o‘chirildi!")


# === KANALLAR RO‘YXATI ===
@dp.callback_query(F.data.startswith("list_"))
async def list_channels(call: CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    channel_type = call.data.replace("list_", "")
    channels = await get_channels(channel_type)

    if not channels:
        await call.message.edit_text("📭 Hech qanday kanal yo‘q.")
        return

    text = "📋 Kanallar ro‘yxati:\n\n"
    for ch in channels:
        text += f"ID: <code>{ch.channel_id}</code>\nLink: {ch.invite_link}\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"{channel_type}_channels")]
    ])
    await call.message.edit_text(text, reply_markup=kb)


# === STARTUP ===
async def main():
    await init_db()
    print("Bot ishga tushdi 🚀")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
