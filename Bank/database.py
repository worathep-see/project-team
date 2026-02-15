# แก้ไฟล์ Bank/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# --- แก้ไขส่วนนี้ ---
# ใช้โฟลเดอร์ปัจจุบันเลย (จะได้ตรงกับ volume ที่ mount ไว้ใน /app/Bank)
DATABASE_URL = "sqlite:///bank.db"
# ------------------

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()