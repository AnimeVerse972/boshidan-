import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy sozlash
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


# === MODELLAR ===
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Majburiy obuna kanallari
class RequiredChannel(Base):
    __tablename__ = "required_channels"
    id = Column(Integer, primary_key=True)
    channel_id = Column(String, unique=True)  # @username yoki ID
    invite_link = Column(String, nullable=True)  # agar private bo‘lsa link


# Asosiy kanallar (bot xabar yuboradigan)
class MainChannel(Base):
    __tablename__ = "main_channels"
    id = Column(Integer, primary_key=True)
    channel_id = Column(String, unique=True)  # @username yoki ID
    invite_link = Column(String, nullable=True)


# Jadval yaratish
Base.metadata.create_all(engine)


# === FUNKSIYALAR ===
def get_user_by_tg_id(tg_id: str):
    return session.query(User).filter_by(telegram_id=tg_id).first()

def add_user(tg_id: str):
    user = User(telegram_id=tg_id)
    session.add(user)
    session.commit()
    return user


# Required channels
def add_required_channel(channel_id: str, invite_link: str = None):
    ch = RequiredChannel(channel_id=channel_id, invite_link=invite_link)
    session.add(ch)
    session.commit()
    return ch

def get_required_channels():
    return session.query(RequiredChannel).all()


# Main channels
def add_main_channel(channel_id: str, invite_link: str = None):
    ch = MainChannel(channel_id=channel_id, invite_link=invite_link)
    session.add(ch)
    session.commit()
    return ch

def get_main_channels():
    return session.query(MainChannel).all()
