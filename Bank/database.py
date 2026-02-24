# แก้ไฟล์ Bank/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool  # ✅ แก้
from models import Base
import os

# --- แก้ไขส่วนนี้ ---
# ใช้โฟลเดอร์ปัจจุบันเลย (จะได้ตรงกับ volume ที่ mount ไว้ใน /app/Bank)
DATABASE_URL = "sqlite:///bank.db"
# ------------------

# ✅ แก้: ใช้ NullPool (ไม่ pool connection) เหมาะกับ SQLite + concurrent requests
# แต่ละ request จะได้ connection ใหม่และคืนทันทีเมื่อเสร็จ ไม่ชนกัน
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,  # ✅ แก้ตรงนี้
    echo=False
)

# ✅ เปิด WAL mode ให้ SQLite รองรับ concurrent reads/writes ได้ดีขึ้น
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()