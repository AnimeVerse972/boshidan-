import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from keep_alive import keep_alive

keep_alive() 
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# SQLAlchemy sozlash
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    tg_id = str(message.from_user.id)
    user = session.query(User).filter_by(telegram_id=tg_id).first()
    if not user:
        user = User(telegram_id=tg_id)
        session.add(user)
        session.commit()
    await message.answer("Salom! Bot ishga tushdi 🚀")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("/start - boshlash\n/help - yordam")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
