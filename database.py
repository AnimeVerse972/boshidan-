import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

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


class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True)
    link = Column(String, unique=True)
    type = Column(String)  # "main" yoki "forced"
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)


# === FUNKSIYALAR ===
def add_user(tg_id: str):
    user = session.query(User).filter_by(telegram_id=tg_id).first()
    if not user:
        user = User(telegram_id=tg_id)
        session.add(user)
        session.commit()


def get_channels(channel_type: str):
    return session.query(Channel).filter_by(type=channel_type).all()


def add_channel(link: str, channel_type: str):
    ch = Channel(link=link, type=channel_type)
    session.add(ch)
    session.commit()


def delete_channel(link: str, channel_type: str):
    ch = session.query(Channel).filter_by(link=link, type=channel_type).first()
    if ch:
        session.delete(ch)
        session.commit()
