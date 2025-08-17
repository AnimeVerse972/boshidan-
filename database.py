import os
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, BigInteger, DateTime, select, delete
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# === DATABASE URL ===
DATABASE_URL = os.getenv("DATABASE_URL")  # misol: postgres://user:pass@host:port/dbname

# === SQLAlchemy asosiy setup ===
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# === MODELLAR ===

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    first_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # "mandatory" yoki "main"
    channel_id = Column(BigInteger, unique=True, nullable=False)  # obuna tekshirish uchun
    invite_link = Column(String, nullable=False)  # foydalanuvchilar uchun
    created_at = Column(DateTime, default=datetime.utcnow)


# === FUNKSIYALAR ===

# Jadval yaratish
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# === CHANNEL FUNKSIYALARI ===

# Kanal qo‘shish
async def add_channel(type_: str, channel_id: int, invite_link: str):
    async with async_session() as session:
        channel = Channel(type=type_, channel_id=channel_id, invite_link=invite_link)
        session.add(channel)
        await session.commit()


# Kanalni o‘chirish
async def delete_channel(channel_id: int):
    async with async_session() as session:
        await session.execute(delete(Channel).where(Channel.channel_id == channel_id))
        await session.commit()


# Barcha kanallarni olish
async def get_channels(type_: str = None):
    async with async_session() as session:
        if type_:
            result = await session.execute(select(Channel).where(Channel.type == type_))
        else:
            result = await session.execute(select(Channel))
        return result.scalars().all()
