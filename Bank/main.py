# Mock Bank API - Pay-Per-Request

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models
import crud
import schemas
from database import get_db, init_db

# สร้างแอป FastAPI
app = FastAPI(title='Mock Bank API', 
              description='Payment system with Pay-Per-Request',
              version='1.0.0')

TOKEN_PRICE = 0.1 # Baht per request

@app.on_event('startup')
def startup_event():
    # เรียกใช้ฟังก์ชันการเริ่มต้นฐานข้อมูล
    init_db()
    print('Mock Bank API is ready!')

@app.post('/users/', response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # สร้างผู้ใช้ใหม่
    try: 
        return crud.create_user(db=db, username=user.username, password=user.password, initial_balance=user.initial_balance)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/login/', response_model=schemas.UserResponse)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    # ตรวจสอบการเข้าสู่ระบบผู้ใข้
    user = crud.authenticate_user(db, username=user_credentials.username, password=user_credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail='Incorrect username or password')
    return user

@app.get('/users/{user_id}', response_model=schemas.UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    # ดึงข้อมุลผู้ใช้ตาม ID
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    return db_user

@app.post('/topup/', response_model=schemas.TopupResponse)
def topup_money(topup_data: schemas.TopupRequest, db: Session = Depends(get_db)):
    # เติมเงินเข้าบัญชีผู้ใช้
    try:
        return crud.topup(db, user_id=topup_data.user_id, amount=topup_data.amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/purchase/', response_model=schemas.PurchaseTokenResponse)
def purchase_tokens(purchase_request: schemas.PurchaseTokenRequest, db: Session = Depends(get_db)):
    # ซื้อโทเค็น Pay-Per-Request
    try:
        result = crud.purchase(db, user_id=purchase_request.user_id, quantity=purchase_request.quantity, price_per_token=TOKEN_PRICE)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/verify/', response_model=schemas.VerifyTokenResponse)
def verify_token(request: schemas.VerifyTokenRequest, db: Session = Depends(get_db)):
    # ตรวจสอบและใช้โทเค็น Pay-Per-Request
    result = crud.verify_and_use_token(db, request.token_id)
    if not result['valid']:
        return result
    return result

@app.get('/users/{user_id}/transaction', response_model=List[schemas.TransactionResponse])
def read_transactions(user_id: int, skip: int=0, limit: int=50, db: Session = Depends(get_db)):
    # ดึงข้อมูลธุรกรรมของผู้ใช้
    return crud.get_users_transactions(db, user_id=user_id, skip=skip, limit=limit)

@app.get('/users/{user_id}/tokens', response_model=List[schemas.TokenResponse])
def read_user_tokens(user_id: int, unused_only: bool = True, db: Session = Depends(get_db)):
    # ดึงข้อมูลโทเค็นของผู้ใช้
    return crud.get_user_token(db, user_id=user_id, unused_only=unused_only)

# [เพิ่ม] ส่วนนี้เพื่อให้รันไฟล์นี้ได้โดยตรง
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)