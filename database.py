import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy sozlash
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# User modeli
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Jadvalni yaratish
Base.metadata.create_all(engine)


# === FUNKSIYALAR ===
def get_user_by_tg_id(tg_id: str):
    return session.query(User).filter_by(telegram_id=tg_id).first()

def add_user(tg_id: str):
    user = User(telegram_id=tg_id)
    session.add(user)
    session.commit()
    return user
