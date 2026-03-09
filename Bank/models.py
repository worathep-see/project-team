# Database models - โครงสร้างตารางทั้งหมด

from sqlalchemy import Column, Integer, String, Float, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    # ตารางผู้ใข้
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    balance = Column(Numeric(precision=12, scale=2), default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    type = Column(String, nullable=False)
    description = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # ความสัมพันธ์กับตารางผู้ใช้
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type='{self.type}')>"
    
class Token(Base):
    # ตารางโทเค็น
    __tablename__ = "Tokens"
    token_id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    price = Column(Numeric(precision=12, scale=2), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)

    # ความสัมพันธ์กับตารางผู้ใช้
    user = relationship("User", back_populates="tokens")

    def __repr__(self):
        status = "USED" if self.used else "AVAILABLE"
        return f"<Token(id='{self.token_id}', user_id={self.user_id}, status={status})>"
