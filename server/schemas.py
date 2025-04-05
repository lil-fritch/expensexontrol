from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional
from datetime import datetime

class ExpenseCreate(BaseModel):
    telegram_id: int 
    name: str
    date: str
    amount_uah: float
    amount_usd: float

    class Config:
        orm_mode = True 
        
    @field_validator('date')
    def validate_date(cls, v):
        try:
            return datetime.strptime(v, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format, should be dd.mm.YYYY")

class ExpenseResponse(BaseModel):
    id: int
    name: str
    date: date
    amount_uah: float
    amount_usd: float

    class Config:
        orm_mode = True 
        
class UserCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    class Config:
        orm_mode = True
        
class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    class Config:
        orm_mode = True