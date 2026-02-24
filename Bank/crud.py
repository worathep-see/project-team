# CRUD operations ฟังก์ชันสำหรับจัดการข้อมูลธนาคาร

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import User, Transaction, Token
from datetime import datetime, timezone, timedelta
import uuid
from typing import List, Optional
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated='auto')
def get_thai_now():
    timezone_thai = timezone(timedelta(hours=7))
    return datetime.now(timezone_thai)

def get_password(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_user(db: Session, username:str, password: str, initial_balance: float= 0.0) -> User:
    # สร้างผู้ใช้ใหม่
    hashed_password = get_password(password)
    try:
        user = User(username=username, hashed_password=hashed_password, balance=initial_balance)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise ValueError('Username already exists')

def authenticate_user(db: Session, username: str, password: str)-> Optional[User]:
    user = db.query(User).filter(User.username==username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_user(db: Session, user_id: int) -> User:

    # ดึงข้อมูลผู้ใช้ตาม ID
    return db.query(User).filter(User.id==user_id).first()

def get_user_by_username(db: Session, username:str) -> User:

    # ดึงข้อมูลผู้ใช้ตามชื่อผู้ใช้
    return db.query(User).filter(User.username==username).first()

def get_all_users(db: Session, skip: int=0, limit: int=100):

    # ดึงข้อมูลผู้ใช้ทั้งหมด
    return db.query(User).offset(skip).limit(limit).all()

def create_transaction(db: Session, user_id:int, amount:float, transaction_type:str, description:str= None) -> Transaction:

    # สร้างธุรกรรมใหม่
    transaction = Transaction(user_id=user_id, amount=amount, type=transaction_type, description=description)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

def get_users_transactions(db: Session, user_id:int, skip:int=0, limit: int=50):

    # ดึงข้อมูลธุรกรรมของผู้ใช้ จากใหม่ไปเก่า
    return db.query(Transaction).filter(Transaction.user_id==user_id).order_by(Transaction.timestamp.desc()).offset(skip).limit(limit).all()

def create_token(db: Session, user_id:int, price_per_token:float, quantity:int=1) -> List[Token]:

    # สร้างโทเค็นใหม่
    new_token = []
    for i in range(quantity):
        token_id = str(uuid.uuid4())
        token = Token(token_id=token_id, user_id=user_id, price=price_per_token)
        db.add(token)
        new_token.append(token)
    db.commit()

    for t in new_token:
        db.refresh(t)
    return new_token

def get_token(db: Session, token_id:str) -> Token:

    # ดึงข้อมูโทเค็นจากโทเค็น ID
    return db.query(Token).filter(Token.token_id==token_id).first()

def verify_and_use_token(db: Session, token_id:str) ->dict:
    rows_updated = db.query(Token).filter(Token.token_id == token_id, Token.used == False).update({'used': True,'used_at': get_thai_now()})
    db.commit()

    if rows_updated == 1:
        token = get_token(db, token_id)
        return {"valid": True, "user_id": token.user_id, "token_id": token_id}
    else:
        token = get_token(db, token_id)
        if not token:
            return {"valid": False, "message": 'Token not found'}
        else:
            return {"valid": False, "message": 'Token already used', "used_at": token.used_at}

def get_user_token(db: Session, user_id:int, unused_only: bool= False) -> List[Token]:

    # ดึงข้อมูลโทเค็นของผู้ใช้

    query = db.query(Token).filter(Token.user_id==user_id)

    if unused_only:
        query = query.filter(Token.used==False)
    return query.order_by(Token.created_at.desc()).all()

def update_balance(db: Session, user_id:int, amount:float, transaction_type:str, description:str= None) -> User:

    # อัพเดทยอดเงินคงเหลือของผู้ใช้และสร้างธุรกรรม
    user = get_user(db, user_id)

    if not user:
        raise ValueError(f"User ID {user_id} not found")
    
    new_balance = user.balance + amount

    # ตรวจสอบว่ามีเงินพอไหม
    if new_balance < 0:
        raise ValueError(f"Insufficient balance: {user.balance}, required: {abs(amount)}")

    # อัพเดทยอดเงินคงเหลือ
    user.balance = new_balance

    # บันทึกธุรกรรม
    create_transaction(db, user_id, amount, transaction_type, description)
    db.commit()
    db.refresh(user)
    return user

def topup(db: Session, user_id:int, amount:float) -> User:

    # เติมเงินเข้าบัญชีผู้ใช้
    if amount <= 0:
        raise ValueError('Top-up amount must be positive')
    return update_balance(db, user_id, amount, "topup", f"Top-up {amount} Baht")

def purchase(db: Session, user_id:int, quantity:int, price_per_token:float) -> dict:
    total_cost = quantity * price_per_token

    # ✅ แก้: Atomic update ป้องกัน Race Condition
    # เช็คและหัก balance ในคำสั่งเดียว จะสำเร็จก็ต่อเมื่อมีเงินพอเท่านั้น
    rows_updated = db.query(User).filter(
        User.id == user_id,
        User.balance >= total_cost
    ).update({"balance": User.balance - total_cost}, synchronize_session="fetch")

    if rows_updated == 0:
        db.rollback()
        user = get_user(db, user_id)
        if not user:
            raise ValueError(f"User ID {user_id} not found")
        raise ValueError(f"Insufficient balance: {user.balance} Baht, "f"required: {total_cost} Baht")

    try:
        transaction = Transaction(user_id=user_id, amount=-total_cost, type="purchase", description=f"Purchase {quantity} tokens")
        db.add(transaction)

        new_tokens = []
        for _ in range(quantity):
            token_id = str(uuid.uuid4())
            token = Token(token_id=token_id, user_id=user_id, price=price_per_token)
            db.add(token)
            new_tokens.append(token_id)

        db.commit()
        db.refresh(get_user(db, user_id))

        user = get_user(db, user_id)
        return {"tokens": new_tokens, "total_cost": total_cost, "remaining_balance": user.balance, "quantity": quantity}

    except Exception as e:
        db.rollback()
        raise e