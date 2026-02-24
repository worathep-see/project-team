from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    # ข้อมูลพื้นฐานของผู้ใช้
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=8)
    initial_balance: float = Field(default=0.0, ge=0)

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        # ตรวจสอบว่า ชื่อผู้ใช้เป็นตัวอักษรและตัวเลขเท่านั้น
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
    
class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    # ข้อมูลผู้ใช้ที่ส่งกลับ
    id: int
    username: str
    balance: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionResponse(BaseModel):
    # ข้อมูลธุรกรรมที่ส่งกลับ
    id: int
    user_id: int
    amount: float
    type: str
    description: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class TopupRequest(BaseModel):
    # คำขอเติมเงิน
    user_id: int = Field(..., gt=0)
    amount: float = Field(..., gt=0)

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Amount must be positive')
        return round(v, 2)  # ทศนิยม 2 ตำแหน่ง

class TopupResponse(BaseModel):
    # ข้อมูลการเติมเงินที่ส่งกลับ (ใช้ UserResponse)
    id: int
    username: str
    balance: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    # ข้อมูลโทเค็นที่ส่งกลับ
    token_id: str
    user_id: int
    price: float
    created_at: datetime
    used: bool
    used_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PurchaseTokenRequest(BaseModel):
    # คำขอซื้อโทเค็น
    user_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v > 100:
            raise ValueError('Cannot purchase more than 100 tokens at once')
        return v

class PurchaseTokenResponse(BaseModel):
    # ข้อมูลการซื้อโทเค็นที่ส่งกลับ
    tokens: List[str]
    total_cost: float
    remaining_balance: float
    quantity: int

class VerifyTokenRequest(BaseModel):
    # คำขอตรวจสอบโทเค็น
    token_id: str = Field(..., description="Token ID to verify")

class VerifyTokenResponse(BaseModel):
    # ข้อมูลการตรวจสอบโทเค็นที่ส่งกลับ
    valid: bool
    user_id: Optional[int] = None
    token_id: Optional[str] = None
    message: Optional[str] = None
    used_at: Optional[datetime] = None
