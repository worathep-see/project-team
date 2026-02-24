# Database models - โครงสร้างตารางทั้งหมด

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone, timedelta

Base = declarative_base()

def get_thai_now():
    timezone_thai = timezone(timedelta(hours=7))
    return datetime.now(timezone_thai)

class User(Base):
    # ตารางผู้ใข้
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=get_thai_now)

    # ความสัมพันธ์กับตารางธุรกรรม
    transactions = relationship("Transaction", back_populates="user")
    tokens = relationship("Token", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', balance={self.balance})>"

class Transaction(Base):
    # ตารางธุรกรรม Type: เติมเงิน, ซื้อ, คืนเงิน
    __tablename__ = 'Transactions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String)
    timestamp = Column(DateTime, default=get_thai_now)

    # ความสัมพันธ์กับตารางผู้ใช้
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type='{self.type}')>"
    
class Token(Base):
    # ตารางโทเค็น
    __tablename__ = "Tokens"
    token_id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=get_thai_now)
    used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)

    # ความสัมพันธ์กับตารางผู้ใช้
    user = relationship("User", back_populates="tokens")

    def __repr__(self):
        status = "USED" if self.used else "AVAILABLE"
        return f"<Token(id='{self.token_id}', user_id={self.user_id}, status={status})>"
    
