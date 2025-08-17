from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # "main" yoki "mandatory"
    channel_id = Column(String, nullable=False)  # -100xxxx
    invite_link = Column(String, nullable=True)  # https://t.me/+xxxx
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def add_channel(channel_type: str, channel_id: str, invite_link: str = None):
    db = SessionLocal()
    channel = Channel(type=channel_type, channel_id=channel_id, invite_link=invite_link)
    db.add(channel)
    db.commit()
    db.refresh(channel)
    db.close()
    return channel


def delete_channel(channel_id: int):
    db = SessionLocal()
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if channel:
        db.delete(channel)
        db.commit()
    db.close()


def get_channels(channel_type: str = None):
    db = SessionLocal()
    if channel_type:
        channels = db.query(Channel).filter(Channel.type == channel_type).all()
    else:
        channels = db.query(Channel).all()
    db.close()
    return channels
